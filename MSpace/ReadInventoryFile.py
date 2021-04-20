import csv


def check_csv_inventory(fname, progressbar, *args):
    with open(fname, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        total_rows = sum(1 for row in csv_reader)

        cols = ["part_id", "name", "description", "location_id", "group_serial", "device_serial",
                "utsa_asset_id", "training_lvl", "qty", "available_to_rent", "in_maintenance", "who_has_it"]

    with open(fname, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        # Check cols order
        row_count = 0
        for row in csv_reader:
            if row_count == 0:
                header = ",".join(row).split(",")
                if cols != header:
                    raise KeyError
                else:
                    pass
                row_count += 1
            percent = int((row_count/total_rows)*100)
            progressbar.setValue(percent)
            row_count += 1

            if percent == 100:
                args[0].toggle()
                args[0].setEnabled(False)
