import config_urls
import upload_file
import upload_raster
import upload_style
import upload_new_layer

def upload_snapshot(
    path_to_file: str,
    file_name_in_server: str,
    resouce_group_parent_id: int,
    raster_layer_name: str,
    srs_id: int,
    style_name: str,
    webmap_id: int
):
    uploaded_file = upload_file.upload_file_from_disk(path_to_file, file_name_in_server)

    raster_layer_id = upload_raster.upload_raster_layer_with_file(uploaded_file, resouce_group_parent_id, raster_layer_name, srs_id)

    style_id = upload_style.create_style_in_layer(raster_layer_id, style_name)

    upload_new_layer.upload_new_layer_webmap(webmap_id, raster_layer_id, style_id)

    return

upload_snapshot(
    "images/output.tif",
    "output.tif",
    config_urls.TEST_RESOURCE_GROUP_ID,
    "test-raster-layer",
    config_urls.SRS_3857,
    "test-style-name",
    config_urls.TEST_WEB_MAP_ID
)
