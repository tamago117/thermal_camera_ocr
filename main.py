import cv2
import easyocr
import csv
from tqdm import tqdm 
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog, messagebox
import re

# settings
cen_region = (65, 10, 55, 40)  # (x, y, width, height)
max_region = (65, 47, 55, 40)  # (x, y, width, height)
min_region = (65, 83, 55, 40)  # (x, y, width, height)
processing_fps = 5  # 1 frame per second

# English only
reader = easyocr.Reader(['en'], gpu=False)

# 小数点を含む数字のみを抽出する関数
def extract_numeric_text(text):
    # 数字と小数点部分を抽出して返す
    numeric_text = re.findall(r'\d+\.\d+|\d+', text)
    return ''.join(numeric_text) if numeric_text else None

def extract_text_from_region(frame, region):
    x, y, w, h = region
    cropped_frame = frame[y:y+h, x:x+w]  # crop region from frame
    temp_image_path = 'temp_region.png'
    cv2.imwrite(temp_image_path, cropped_frame)  # save cropped image to disk (temporary)

    # get text from cropped image
    results = reader.readtext(temp_image_path)
    
    if results:
        raw_text = results[0][1]
        return extract_numeric_text(raw_text)  # 小数点を含む数字のみを抽出
    return None

def extract_temperatures_from_frame(frame):
    # extract text from each region
    cen_value = extract_text_from_region(frame, cen_region)
    max_value = extract_text_from_region(frame, max_region)
    min_value = extract_text_from_region(frame, min_region)
    
    return cen_value, max_value, min_value

def process_video(video_path, csv_output, processing_fps=processing_fps):
    # open video file
    cap = cv2.VideoCapture(video_path)
    
    # get video properties
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if processing_fps > original_fps:
        print("processing FPS cannot be higher than the original FPS. Setting processing FPS to original FPS.")
        processing_fps = original_fps
    
    # calculate the frame interval to match the lower processing FPS
    frame_interval = int(original_fps / processing_fps)
    
    # create CSV file and write header
    with open(csv_output, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time (s)', 'Cen', 'Max', 'Min'])
        
        # process each frame at a lower FPS
        for frame_number in tqdm(range(0, total_frames, frame_interval), desc="Processing frames"):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = round(frame_number / original_fps, 2)

            # extract temperatures from each region
            cen_value, max_value, min_value = extract_temperatures_from_frame(frame)

            if cen_value and max_value and min_value:
                writer.writerow([timestamp, cen_value, max_value, min_value])

    cap.release()
    print(f"処理が完了しました。データは {csv_output} に保存されました。")

def select_video_file():
    file_path = filedialog.askopenfilename(
        title="select a video file",
        filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
    )
    if file_path:
        save_csv(file_path)


def save_csv(video_file):
    save_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Save CSV file"
    )
    if save_path:
        process_video(video_file, save_path, processing_fps=processing_fps)

def setup_gui():
    root = tk.Tk()
    root.withdraw()

    select_video_file()

if __name__ == "__main__":
    setup_gui()