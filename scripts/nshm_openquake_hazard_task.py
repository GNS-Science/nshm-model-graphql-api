#!/usr/bin/env python


# This file has been automatically generated.
# Instead of changing it, create a file called import_helper.py
# and put there a class called ImportHelper(object) in it.
#
# This class will be specially casted so that instead of extending object,
# it will actually extend the class BasicImportHelper()
#
# That means you just have to overload the methods you want to
# change, leaving the other ones intact.
#
# Something that you might want to do is use transactions, for example.
#
# Also, don't forget to add the necessary Django imports.
#
# This file was generated with the following command:
# manage.py dumpscript nshm.OpenquakeHazardTask
#
# to restore it, run
# manage.py runscript module_name.this_script_name
#
# example: if manage.py is at ./manage.py
# and the script is at ./some_folder/some_script.py
# you must make sure ./some_folder/__init__.py exists
# and run  ./manage.py runscript some_folder.some_script
import os
import sys
from django.db import transaction
# from decimal import Decimal
# from django.contrib.contenttypes.models import ContentType

import csv
import pathlib


class BasicImportHelper:
    def pre_import(self):
        pass

    @transaction.atomic
    def run_import(self, import_data):
        import_data()

    def post_import(self):
        pass

    def locate_similar(self, current_object, search_data):
        # You will probably want to call this method from save_or_locate()
        # Example:
        #   new_obj = self.locate_similar(the_obj, {"national_id": the_obj.national_id } )

        the_obj = current_object.__class__.objects.get(**search_data)
        return the_obj

    def locate_object(
        self,
        original_class,
        original_pk_name,
        the_class,
        pk_name,
        pk_value,
        obj_content,
    ):
        # You may change this function to do specific lookup for specific objects
        #
        # original_class class of the django orm's object that needs to be located
        # original_pk_name the primary key of original_class
        # the_class      parent class of original_class which contains obj_content
        # pk_name        the primary key of original_class
        # pk_value       value of the primary_key
        # obj_content    content of the object which was not exported.
        #
        # You should use obj_content to locate the object on the target db
        #
        # An example where original_class and the_class are different is
        # when original_class is Farmer and the_class is Person. The table
        # may refer to a Farmer but you will actually need to locate Person
        # in order to instantiate that Farmer
        #
        # Example:
        #   if the_class == SurveyResultFormat or the_class == SurveyType or the_class == SurveyState:
        #       pk_name="name"
        #       pk_value=obj_content[pk_name]
        #   if the_class == StaffGroup:
        #       pk_value=8

        search_data = {pk_name: pk_value}
        the_obj = the_class.objects.get(**search_data)
        # print(the_obj)
        return the_obj

    def save_or_locate(self, the_obj):
        # Change this if you want to locate the object in the database
        try:
            the_obj.save()
        except:  # noqa
            print("---------------")
            print("Error saving the following object:")
            print(the_obj.__class__)
            print(" ")
            print(the_obj.__dict__)
            print(" ")
            print(the_obj)
            print(" ")
            print("---------------")

            raise
        return the_obj


importer = None
try:
    import import_helper

    # We need this so ImportHelper can extend BasicImportHelper, although import_helper.py
    # has no knowlodge of this class
    importer = type(
        "DynamicImportHelper", (import_helper.ImportHelper, BasicImportHelper), {}
    )()
except ImportError as e:
    # From Python 3.3 we can check e.name - string match is for backward compatibility.
    if "import_helper" in str(e):
        importer = BasicImportHelper()
    else:
        raise

try:
    import dateutil.parser
    # from dateutil.tz import tzoffset
except ImportError:
    print("Please install python-dateutil")
    sys.exit(os.EX_USAGE)


def run():
    importer.pre_import()
    importer.run_import(import_data)
    importer.post_import()


def import_data():
    # Initial Imports
    # Processing model: nshm.models.OpenquakeHazardTask
    from nshm.models import OpenquakeHazardTask, SeismicHazardModel

    p = pathlib.Path("NZSHM22 Beavan Job Control - OQ Hazard.csv")
    assert p.exists()
    with open(p, "r") as csv_file:

        for itm in csv.DictReader(csv_file):
            if int(itm["Invalid"]) == 1:
                continue

            obj = OpenquakeHazardTask(
                date=dateutil.parser.parse(itm["Date"]),
                general_task_id=itm["GenTask"],
                config_info=itm["Runzi Config"],
                notes=itm["Notes"],
            )
            # print('OBJ', obj, itm['part_of'])
            if itm["part_of"]:
                found = list(
                    SeismicHazardModel.objects.filter(version__exact=itm["part_of"])
                )
                if found:
                    shm = found[0]
                else:
                    shm = SeismicHazardModel(version=itm["part_of"])
                    shm.save()

                obj.part_of = shm
            obj.save()
