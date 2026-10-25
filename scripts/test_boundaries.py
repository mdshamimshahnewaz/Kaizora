import unittest

from check_boundaries import violations


class BoundaryTests(unittest.TestCase):
    def test_accepts_public_interface_and_own_models(self):
        source = "from modules.timesheets.interfaces import approved_work\nfrom .models import Invoice"
        self.assertEqual(violations(source, "modules.billing.services"), [])

    def test_rejects_private_absolute_and_relative_imports(self):
        for source in [
            "from modules.timesheets.models import TimeEntry",
            "import modules.timesheets.models",
            "from ..timesheets.models import TimeEntry",
            "from modules.timesheets import models",
            "from modules import timesheets",
        ]:
            with self.subTest(source=source):
                self.assertTrue(violations(source, "modules.billing.services"))

    def test_accepts_relative_public_interface(self):
        self.assertEqual(
            violations(
                "from ..timesheets import interfaces", "modules.billing.services"
            ),
            [],
        )
