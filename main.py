from src import vegetation_remote_sensing

def main():
    app = vegetation_remote_sensing.VegetationRemoteSensing()

    if app is None:
        return

    # начальная и конечная дата съемки
    start_date = "2024-08-01"
    end_date = "2024-08-06"

    # интересующая область задается прямоугольником
    # левый нижний угол
    lower_left_latitude = 67.063152
    lower_left_longitude = 35.167236
    # правый верхний угол
    upper_right_latitude = 67.995225
    upper_right_longitude = 38.045654

    # 67.063152, 35.167236 - левый нижний угол прямоугольника
    # 67.995225, 38.045654 - правый верхний угол прямоугольника
    app.add_vegetation_to_the_webmap(
        start_date,
        end_date,
        lower_left_latitude,
        lower_left_longitude,
        upper_right_latitude,
        upper_right_longitude,
    )

    return

if __name__ == "__main__":
    main()

def continue_images_processing():
    app = vegetation_remote_sensing.VegetationRemoteSensing()

    if app is None:
        return

    downloaded_images_info_path = "recovery_data/2024-03-24_downloaded_images.json"

    app.continue_process_images(downloaded_images_info_path)

    return

def continue_images_uploading():
    app = vegetation_remote_sensing.VegetationRemoteSensing()

    if app is None:
        return

    processed_images_info_path = "recovery_data/2024-03-24_processed_images.json"

    app.continue_upload_to_geoportal(processed_images_info_path)

    return
