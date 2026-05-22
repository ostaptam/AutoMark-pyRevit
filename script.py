from pyrevit import revit, DB, forms

doc = revit.doc


def get_instances(category):
    return (
        DB.FilteredElementCollector(doc)
        .OfCategory(category)
        .WhereElementIsNotElementType()
        .ToElements()
    )


def get_level(element):
    level_id = element.LevelId

    if level_id and level_id != DB.ElementId.InvalidElementId:
        return doc.GetElement(level_id)

    host = element.Host

    if host:
        host_level_id = host.LevelId

        if host_level_id and host_level_id != DB.ElementId.InvalidElementId:
            return doc.GetElement(host_level_id)

    return None


def get_level_code(level):
    if not level:
        return "00"

    name = level.Name

    digits = ""

    for ch in name:
        if ch.isdigit():
            digits += ch

    if digits:
        return digits.zfill(2)

    return "00"


def number_elements(elements, prefix):
    grouped = {}

    for element in elements:
        level = get_level(element)
        level_code = get_level_code(level)

        if level_code not in grouped:
            grouped[level_code] = []

        grouped[level_code].append(element)

    updated = 0

    with revit.Transaction("Number " + prefix):
        for level_code in sorted(grouped.keys()):
            items = grouped[level_code]

            def get_xy(element):
                location = element.Location

                if location and hasattr(location, "Point"):
                    pt = location.Point
                    return (pt.Y, -pt.X)

                return (999999, 999999)

            items = sorted(items, key=get_xy)

            counter = 1

            for item in items:
                mark_param = item.LookupParameter("Mark")

                if mark_param:
                    new_mark = prefix + "-" + level_code + "-" + str(counter).zfill(3)
                    mark_param.Set(new_mark)
                    updated += 1
                    counter += 1

    return updated


doors = get_instances(DB.BuiltInCategory.OST_Doors)
windows = get_instances(DB.BuiltInCategory.OST_Windows)

import os
from pyrevit import script

class AutoMarkWindow(forms.WPFWindow):
    def __init__(self):
        xamlfile = script.get_bundle_file('ui.xaml')
        forms.WPFWindow.__init__(self, xamlfile)

        self.run_tool = False

        self.btn_run.Click += self.run_click
        self.btn_cancel.Click += self.cancel_click

    def run_click(self, sender, args):
        self.run_tool = True
        self.Close()

    def cancel_click(self, sender, args):
        self.Close()


window = AutoMarkWindow()
window.ShowDialog()

if window.run_tool:

    updated_doors = number_elements(doors, "D")
    updated_windows = number_elements(windows, "W")

    forms.alert(
        "AutoMark Report\n\n"
        + "Doors updated: " + str(updated_doors) + "\n"
        + "Windows updated: " + str(updated_windows)
    )
else:
    forms.alert("Cancelled")