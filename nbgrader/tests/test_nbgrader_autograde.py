from .base import TestBase
from nbgrader.api import Gradebook

from nose.tools import assert_equal

import os
import shutil
import datetime

class TestNbgraderAutograde(TestBase):

    def _setup_db(self):
        dbpath = self._init_db()
        gb = Gradebook(dbpath)
        gb.add_assignment("Problem Set 1")
        gb.add_student("foo")
        gb.add_student("bar")
        return dbpath

    def test_help(self):
        """Does the help display without error?"""
        with self._temp_cwd():
            self._run_command("nbgrader autograde --help-all")

    def test_missing_student(self):
        """Is an error thrown when the student is missing?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1"'.format(dbpath),
                retcode=1)

    def test_missing_assignment(self):
        """Is an error thrown when the assignment is missing?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db="{}" '
                '--student=foo'.format(dbpath),
                retcode=1)

    def test_single_file(self):
        """Can a single file be graded?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--student=foo'.format(dbpath))

            assert os.path.isfile("submitted.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            notebook = gb.find_submission_notebook("submitted", "Problem Set 1", "foo")
            assert_equal(notebook.score, 1, "autograded score is incorrect")
            assert_equal(notebook.max_score, 3, "maximum score is incorrect")
            assert_equal(notebook.needs_manual_grade, True, "should need manual grade")

    def test_single_file_with_checksum_autograding(self):
        """Can a single file be graded using checksum autograding?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--SaveAutoGrades.checksum_autograding=True '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--student=foo'.format(dbpath))

            assert os.path.isfile("submitted.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            notebook = gb.find_submission_notebook("submitted", "Problem Set 1", "foo")
            assert_equal(notebook.score, 1, "autograded score is incorrect")
            assert_equal(notebook.max_score, 3, "maximum score is incorrect")
            assert_equal(notebook.needs_manual_grade, False, "should need manual grade")

    def test_overwrite(self):
        """Can a single file be graded and overwrite cells?"""
        with self._temp_cwd(["files/submitted.ipynb", "files/submitted-changed.ipynb"]):
            shutil.move('submitted.ipynb', 'teacher.ipynb')
            shutil.move('submitted-changed.ipynb', 'submitted-bar.ipynb')
            dbpath = self._setup_db()

            # first assign it and save the cells into the database
            self._run_command(
                'nbgrader assign teacher.ipynb '
                '--save-cells '
                '--output=submitted-foo.ipynb '
                '--db="{}" '
                '--assignment="Problem Set 1" '.format(dbpath))

            # now run the autograder
            self._run_command(
                'nbgrader autograde submitted-foo.ipynb '
                '--overwrite-cells '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--AssignmentExporter.notebook_id=teacher '
                '--student=foo'.format(dbpath))
            self._run_command(
                'nbgrader autograde submitted-bar.ipynb '
                '--overwrite-cells '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--AssignmentExporter.notebook_id=teacher '
                '--student=bar'.format(dbpath))

            assert os.path.isfile("submitted-foo.nbconvert.ipynb")
            assert os.path.isfile("submitted-bar.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            notebook = gb.find_submission_notebook("teacher", "Problem Set 1", "foo")
            assert_equal(notebook.score, 1, "autograded score is incorrect")
            assert_equal(notebook.max_score, 3, "maximum score is incorrect")
            assert_equal(notebook.needs_manual_grade, False, "should need manual grade")

            notebook = gb.find_submission_notebook("teacher", "Problem Set 1", "bar")
            assert_equal(notebook.score, 1, "autograded score is incorrect")
            assert_equal(notebook.max_score, 3, "maximum score is incorrect")
            assert_equal(notebook.needs_manual_grade, True, "should need manual grade")

    def test_timestamp(self):
        """Can the timestamp on a submission be set?"""
        with self._temp_cwd(["files/submitted.ipynb"]):
            now = datetime.datetime.now().isoformat()
            dbpath = self._setup_db()
            self._run_command(
                'nbgrader autograde submitted.ipynb '
                '--timestamp="{}" '
                '--db="{}" '
                '--assignment="Problem Set 1" '
                '--student=foo'.format(now, dbpath))

            assert os.path.isfile("submitted.nbconvert.ipynb")

            gb = Gradebook(dbpath)
            submission = gb.find_submission("Problem Set 1", "foo")
            assert submission.timestamp.isoformat() == now
