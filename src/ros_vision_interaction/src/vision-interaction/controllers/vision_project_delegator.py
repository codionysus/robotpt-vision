#!/usr/bin/env python3.8
import datetime
import logging
import math
import vision_project_tools.reading_task_tools as reading_task_tools

from vision_project_tools.constants import DatabaseKeys, INITIAL_STATE_DB, Interactions
from vision_project_tools.reading_task_tools import TaskDataKeys, Tasks

logging.basicConfig(level=logging.INFO)


class VisionProjectDelegator:

    def __init__(
            self,
            statedb,
            update_window_seconds=5,
            scheduled_window_minutes=15,
            minutes_between_interactions=1,
            max_num_of_prompted_per_day=3,
            score_window=10
    ):
        self._state_database = statedb
        self._update_window_seconds = datetime.timedelta(seconds=update_window_seconds)
        self._scheduled_window_minutes = datetime.timedelta(minutes=scheduled_window_minutes)
        self._minutes_between_interactions = datetime.timedelta(minutes=minutes_between_interactions)
        self._max_num_of_prompted_per_day = max_num_of_prompted_per_day
        self._score_window = score_window

        self._is_run_interaction = False

        # for testing purposes
        self._reset_database()

        self._state_database.set(DatabaseKeys.LAST_UPDATE_DATETIME, datetime.datetime.now())
        self._state_database.set(DatabaseKeys.CURRENT_READING_INDEX, datetime.datetime.now().weekday())

        # self._state_database.set(DatabaseKeys.VIDEO_TO_PLAY, "light")
        self.new_day_update()

    def update(self):
        if self._is_new_day():
            self.new_day_update()
        self._state_database.set(DatabaseKeys.LAST_UPDATE_DATETIME, datetime.datetime.now())

    def _is_new_day(self):
        return datetime.datetime.now().date() > self._state_database.get(DatabaseKeys.LAST_UPDATE_DATETIME).date()

    def new_day_update(self):
        self._daily_state_update()
        self._update_act_variables()
        self._daily_reading_task_data_update()
        self._state_database.set(DatabaseKeys.NUM_OF_PROMPTED_TODAY, 0)
        self._state_database.set(DatabaseKeys.PERSEVERANCE_COUNTER, 0)
        self._state_database.set(DatabaseKeys.FEELINGS_INDEX, None)
        self._state_database.set(DatabaseKeys.IS_PUBLISHED_CHOICES_TODAY, False)

    def _daily_state_update(self):
        # update reading task index if reading task has been done
        if self._state_database.get(DatabaseKeys.IS_DONE_EVAL_TODAY):
            current_index = self._state_database.get(DatabaseKeys.CURRENT_READING_INDEX)
            new_index = (current_index + 1) % 6
            self._state_database.set(DatabaseKeys.CURRENT_READING_INDEX, new_index)
        keys_to_check = {
            DatabaseKeys.IS_DONE_EVAL_TODAY: DatabaseKeys.NUM_OF_DAYS_SINCE_LAST_EVAL,
            DatabaseKeys.IS_DONE_PROMPTED_TODAY: DatabaseKeys.NUM_OF_DAYS_SINCE_LAST_PROMPT,
            DatabaseKeys.IS_DONE_PERSEVERANCE_TODAY: DatabaseKeys.NUM_OF_DAYS_SINCE_LAST_PERSEVERANCE,
            DatabaseKeys.IS_DONE_MINDFULNESS_TODAY: DatabaseKeys.NUM_OF_DAYS_SINCE_LAST_MINDFULNESS,
            DatabaseKeys.IS_DONE_GOAL_SETTING_TODAY: DatabaseKeys.NUM_OF_DAYS_SINCE_LAST_GOAL_SETTING
        }
        for key in keys_to_check:
            if not self._state_database.get(key):
                old_value = self._state_database.get(keys_to_check[key])
                self._state_database.set(keys_to_check[key], old_value + 1)
            else:
                self._state_database.set(keys_to_check[key], 0)
            self._state_database.set(key, False)

    def _update_act_variables(self):
        last_5_scores = self._state_database.get(DatabaseKeys.LAST_5_EVAL_SCORES)
        if len(last_5_scores) == 5:
            last_5_scores.pop(0)
        last_5_scores.append(self._state_database.get(DatabaseKeys.CURRENT_EVAL_SCORE))
        self._state_database.set(DatabaseKeys.LAST_5_EVAL_SCORES, last_5_scores)

    def _daily_reading_task_data_update(self):
        # last_5_scores = self._state_database.get(DatabaseKeys.LAST_5_EVAL_SCORES)
        # average_score = sum(last_5_scores)/len(last_5_scores)
        # current_score = self._state_database.get(DatabaseKeys.CURRENT_EVAL_SCORE)
        grit_feedback_index = 0  # STABLE, default value for first reading task
        # if current_score is not None:
        #     if current_score < average_score - self._score_window:
        #         grit_feedback_index = 1  # DECLINED
        #     elif current_score > average_score + self._score_window:
        #         grit_feedback_index = 2  # IMPROVED
        # self._state_database.set(DatabaseKeys.GRIT_FEEDBACK_INDEX, grit_feedback_index)
        # set reading task data for the new day
        task_id = reading_task_tools.get_new_day_reading_task(self._state_database)
        self._state_database.set(DatabaseKeys.CURRENT_READING_ID, task_id)
        task_color = reading_task_tools.get_reading_task_data_value(self._state_database, task_id, TaskDataKeys.COLOR)
        self._state_database.set(DatabaseKeys.CURRENT_READING_COLOR, task_color)

    def get_interaction_type(self):
        logging.info("Determining interaction type")
        if self._is_first_interaction():
            interaction_type = Interactions.FIRST_INTERACTION
        elif self._is_time_for_scheduled_interaction():
            interaction_type = Interactions.SCHEDULED_INTERACTION
        elif self._is_run_too_many_prompted():
            interaction_type = Interactions.TOO_MANY_PROMPTED
        elif self._is_run_prompted_interaction():
            interaction_type = Interactions.PROMPTED_INTERACTION
        elif self._is_ask_to_do_scheduled():
            interaction_type = Interactions.ASK_TO_DO_SCHEDULED
        else:
            interaction_type = None
        return interaction_type
        # return Interactions.EVALUATION

    def _is_first_interaction(self):
        return not self._state_database.is_set(DatabaseKeys.FIRST_INTERACTION_DATETIME)

    def _is_time_for_scheduled_interaction(self):
        if not self._state_database.get(DatabaseKeys.NEXT_CHECKIN_DATETIME):
            return False

        if self._state_database.get(DatabaseKeys.IS_DONE_EVAL_TODAY):
            is_time = False
        else:
            is_in_update_window = self._is_in_window(
                self._state_database.get(DatabaseKeys.NEXT_CHECKIN_DATETIME),
                self._update_window_seconds,
                datetime.datetime.now()
            )
            is_prompted_in_scheduled_window = self._is_in_window(
                self._state_database.get(DatabaseKeys.NEXT_CHECKIN_DATETIME),
                self._scheduled_window_minutes,
                datetime.datetime.now()
            )

            is_time = is_in_update_window or \
                      (is_prompted_in_scheduled_window and not self._state_database.get(
                          DatabaseKeys.IS_DONE_EVAL_TODAY) and
                       self._state_database.get(DatabaseKeys.IS_PROMPTED_BY_USER))

        return is_time

    def _is_ask_to_do_scheduled(self):
        is_in_scheduled_window = self._is_in_window(
            self._state_database.get(DatabaseKeys.NEXT_CHECKIN_DATETIME),
            self._scheduled_window_minutes,
            datetime.datetime.now()
        )
        return self._state_database.get(DatabaseKeys.IS_PROMPTED_BY_USER) and \
               not self._state_database.get(DatabaseKeys.IS_DONE_EVAL_TODAY) and \
               not is_in_scheduled_window

    def _is_run_prompted_interaction(self):
        return self._state_database.get(DatabaseKeys.IS_PROMPTED_BY_USER) and \
               self._state_database.get(DatabaseKeys.IS_DONE_EVAL_TODAY) and \
               self._state_database.get(DatabaseKeys.NUM_OF_PROMPTED_TODAY) < self._max_num_of_prompted_per_day

    def _is_run_too_many_prompted(self):
        return self._state_database.get(DatabaseKeys.IS_PROMPTED_BY_USER) and \
               self._state_database.get(DatabaseKeys.NUM_OF_PROMPTED_TODAY) >= self._max_num_of_prompted_per_day

    def _is_in_window(self, center, window, time_to_check):
        start_time = center - window
        end_time = center + window
        return start_time <= time_to_check <= end_time

    def _reset_database(self):
        for key in INITIAL_STATE_DB:
            self._state_database.set(key, INITIAL_STATE_DB[key])
