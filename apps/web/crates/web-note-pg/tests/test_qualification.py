import copy
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from qualification import REQUIRED, discover, qualify_report

class NativeQualification(unittest.TestCase):
    def discovery(self):
        cases={name:{"ignored":False,"filter-match":{"status":"matches"}} for name in REQUIRED["stateful"]}
        return {"test-count":len(cases),"rust-suites":{"crate::stateful":{"binary-name":"stateful","status":"listed","testcases":cases}}}

    def test_discovery_fail_closed(self):
        original=self.discovery()
        self.assertEqual(discover(original,("stateful",)),{"stateful":{("crate::stateful",name) for name in REQUIRED["stateful"]}})
        for mutate in (
            lambda d: d.update({"test-count":0}),
            lambda d: d["rust-suites"].clear(),
            lambda d: d["rust-suites"].update({"crate::unknown":{"binary-name":"unknown","status":"listed","testcases":{"new":{"ignored":False,"filter-match":{"status":"matches"}}}}}),

            lambda d: d["rust-suites"]["crate::stateful"]["testcases"]["generated_native_trajectories"].update(ignored=True),
            lambda d: d["rust-suites"]["crate::stateful"]["testcases"]["generated_native_trajectories"].update({"filter-match":{"status":"mismatch"}}),
        ):
            data=copy.deepcopy(original)
            mutate(data)
            with self.assertRaises(ValueError):
                discover(data,("stateful",))

    def test_report_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"report.xml"
            expected={("crate::stateful","generated_native_trajectories")}
            with self.assertRaises(FileNotFoundError):
                qualify_report(path,expected)
            def root():
                r=ET.Element("testsuites",tests="1",skipped="0",failures="0",errors="0",uuid="test-run")
                s=ET.SubElement(r,"testsuite",tests="1",skipped="0",failures="0",errors="0")
                ET.SubElement(s,"testcase",classname="crate::stateful",name="generated_native_trajectories")
                return r
            r=root()
            ET.ElementTree(r).write(path)
            self.assertEqual(qualify_report(path,expected)["status"],"PASS")
            for mutate in (
                lambda r:r.set("skipped","1"),
                lambda r:r.set("failures","1"),
                lambda r:r.set("errors","1"),
                lambda r:r.set("tests","0"),
                lambda r:r.attrib.pop("uuid"),
                lambda r:r.find(".//testcase").set("name","wrong"),
                lambda r:r.find("testsuite").append(copy.deepcopy(r.find(".//testcase"))),
                lambda r:ET.SubElement(r.find(".//testcase"),"skipped"),
                lambda r:ET.SubElement(r.find(".//testcase"),"flakyFailure"),
            ):
                r=root();mutate(r);ET.ElementTree(r).write(path)
                with self.assertRaises(ValueError):
                    qualify_report(path,expected)

if __name__=="__main__":
    unittest.main()
