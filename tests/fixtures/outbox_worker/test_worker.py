import unittest

from worker import CrashAfterEffect, Worker, connect, count_effects, seed


class WorkerFixtureTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        seed(self.db)
        self.worker = Worker(self.db)

    def tearDown(self):
        self.db.close()

    def test_normal_run_has_one_effect_and_marks_message(self):
        self.assertTrue(self.worker.run_once())
        self.assertEqual(count_effects(self.db), 1)
        self.assertIsNotNone(self.db.execute("SELECT processed_at FROM outbox").fetchone()[0])
        self.assertEqual(self.db.execute("SELECT state FROM jobs").fetchone()[0], "done")

    @unittest.expectedFailure
    def test_ticket_crash_retry_is_exactly_once(self):
        with self.assertRaises(CrashAfterEffect):
            self.worker.run_once(crash_after_effect=True)
        self.worker.run_once()
        self.assertEqual(count_effects(self.db), 1)

    @unittest.expectedFailure
    def test_ticket_requires_atomic_crash_recovery(self):
        with self.assertRaises(CrashAfterEffect):
            self.worker.run_once(crash_after_effect=True)
        row = self.db.execute("SELECT processed_at, attempts FROM outbox").fetchone()
        self.assertIsNone(row[0], "a crash must leave the message retryable")
        self.assertEqual(row[1], 0, "a crash must roll back the acknowledgement transaction")


if __name__ == "__main__":
    unittest.main()
