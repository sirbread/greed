import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import os
from datetime import datetime, timezone

def generate_round_graphs(rounds_data, min_num, max_num, output_folder="static/graphs"):
    os.makedirs(output_folder, exist_ok=True)
    image_filenames = []
    for i, round_data in enumerate(rounds_data, 1):
        counts = []
        points = []
        max_y = 0
        for n in range(min_num, max_num+1):
            count = round_data.get(n, 0)
            counts.append(count)
            pt = n / count if count > 0 else 0
            points.append(pt)
            max_y = max(max_y, count, pt)
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(range(min_num, max_num+1), counts, label="count", color="red")
        ax.plot(range(min_num, max_num+1), points, label="points", color="blue")
        ax.legend()
        ax.set_xlabel("number selected in range")
        ax.set_ylabel("value")
        utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ax.set_title(f"round {i} - {utc_now}")
        ax.set_ylim(0, int(max_y+1))
        img_name = f"round_{i}.png"
        img_path = os.path.join(output_folder, img_name)
        fig.tight_layout()
        plt.savefig(img_path)
        plt.close(fig)
        image_filenames.append(img_name)
    return image_filenames