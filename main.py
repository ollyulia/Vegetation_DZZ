from src import vegetation_remote_sensing

def main():
    app = vegetation_remote_sensing.VegetationRemoteSensing()

    if app is None:
        return

    # начальная и конечная дата съемки
    start_date = "2024-08-20"
    end_date = "2024-08-22"

    # интересующая область задается прямоугольником
    # Кольский полуостров
    # левый нижний угол
    # 66.213585, 27.771668
    lower_left_latitude = 66.372602
    lower_left_longitude = 29.540467
    # правый верхний угол
    # 69.549744, 41.416688
    upper_right_latitude = 69.549744
    upper_right_longitude = 41.416688

    start_date = "2024-07-20"
    end_date = "2024-07-30"

    lower_left_latitude = 66.240158
    lower_left_longitude = 32.067323
    upper_right_latitude = 69.287122
    upper_right_longitude = 41.559510

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

    start_date = "2024-08-14"
    end_date = "2024-08-15"

    lower_left_latitude = 68.562252
    lower_left_longitude = 31.50702
    upper_right_latitude = 68.915808
    upper_right_longitude = 37.134767

    downloaded_images_info_path = "recovery_data/2025-05-18.json"

    path = "images/2025-05-20/2024-08-14_2024-08-15_68.562252:31.50702_68.915808:37.134767"

    app.continue_process_images(
        downloaded_images_info_path,
        path,
        lower_left_latitude,
        lower_left_longitude,
        upper_right_latitude,
        upper_right_longitude,
        start_date,
        end_date,
    )

    return

def continue_images_uploading():
    app = vegetation_remote_sensing.VegetationRemoteSensing()

    if app is None:
        return

    start_date = "2024-08-14"
    end_date = "2024-08-15"

    lower_left_latitude = 68.562252
    lower_left_longitude = 31.50702
    upper_right_latitude = 69.219015
    upper_right_longitude = 31.50702

    processed_images_info_path = "recovery_data/2025-05-30_17-29-26_processed_images.json"

    app.continue_upload_to_geoportal(
        processed_images_info_path,
        start_date,
        end_date,
        lower_left_latitude,
        lower_left_longitude,
        upper_right_latitude,
        upper_right_longitude
    )

    return


if __name__ == "__main__":
    main()
