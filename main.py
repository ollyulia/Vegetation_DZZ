from src import vegetation_remote_sensing

def main():
    app = vegetation_remote_sensing.VegetationRemoteSensing()

    if app is None:
        return

    # начальная и конечная дата съемки
    start_date = "2024-08-14"
    end_date = "2024-08-15"

    # интересующая область задается прямоугольником
    # Кольский полуостров
    # левый нижний угол
    # 66.213585, 27.771668
    lower_left_latitude = 68.562252
    lower_left_longitude = 31.507020
    # правый верхний угол
    # 69.549744, 41.416688
    upper_right_latitude = 69.219015
    upper_right_longitude = 33.924012

    app.add_vegetation_to_the_webmap_from_earth_explorer(
        start_date,
        end_date,
        lower_left_latitude,
        lower_left_longitude,
        upper_right_latitude,
        upper_right_longitude,
    )

    return

def continue_images_processing():
    app = vegetation_remote_sensing.VegetationRemoteSensing()

    if app is None:
        return

    downloaded_images_info_path = "recovery_data/2024-03-25_downloaded_images.json"

    app.continue_process_images(downloaded_images_info_path)

    return

def continue_images_uploading():
    app = vegetation_remote_sensing.VegetationRemoteSensing()

    if app is None:
        return

    processed_images_info_path = "recovery_data/2024-03-24_processed_images.json"

    app.continue_upload_to_geoportal(processed_images_info_path)

    return


if __name__ == "__main__":
    main()
