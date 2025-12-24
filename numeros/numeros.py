import csv
import math

input_file = "numeros.csv"
total_lines = 277225
num_files = 20
lines_per_file = math.ceil(total_lines / num_files)

with open(input_file, "r", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)  # "missing_id"

    for i in range(num_files):
        output_name = f"numeros_{i + 1}.csv"

        with open(output_name, "w", newline="") as out_f:
            writer = csv.writer(out_f)
            writer.writerow(header)

            count = 0
            for row in reader:
                writer.writerow(row)
                count += 1
                if count >= lines_per_file:
                    break
