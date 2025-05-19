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
    lower_left_latitude = 66.213585
    lower_left_longitude = 27.771668
    # правый верхний угол
    # 69.549744, 41.416688
    upper_right_latitude = 69.549744
    upper_right_longitude = 41.416688

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

    start_date = "2024-08-20"
    end_date = "2024-08-22"

    lower_left_latitude = 66.213585
    lower_left_longitude = 27.771668
    upper_right_latitude = 69.549744
    upper_right_longitude = 41.416688

    downloaded_images_info_path = "recovery_data/2025-05-18.json"

    path = "images/2025-05-18/2024-08-20_2024-08-22_66.213585:27.771668_69.549744:27.771668"

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

    start_date = "2024-08-20"
    end_date = "2024-08-22"

    lower_left_latitude = 66.213585
    lower_left_longitude = 27.771668
    upper_right_latitude = 69.549744
    upper_right_longitude = 41.416688

    processed_images_info_path = "recovery_data/2025-05-18-processed.json"

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
    continue_images_uploading()
