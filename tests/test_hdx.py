from povertymapping.hdx import download_hdx, get_hdx_file
from pathlib import Path

def test_download_hdx(tmpdir, mocker):
    mocker.patch('povertymapping.hdx.get_iso3_code', return_value='TLS')
    mock_resource = dict(
        name='tls_general_2020_geotiff.zip',
        download_url='https://example.com/tls_general_2020_geotiff.zip'
    )  
    mock_resources = [mock_resource] 

    mock_dataset = mocker.MagicMock()
    mock_dataset.get_resources = mocker.MagicMock(return_value=mock_resources)
    mocker.patch('hdx.data.dataset.Dataset.read_from_hdx', return_value=mock_dataset)
    mock_zipped_file = mocker.MagicMock()
    mocker.patch('povertymapping.hdx.urlretrieve', return_value=(mock_zipped_file,None,None))
    cache_dir = str(tmpdir/'this-directory-does-not-exist')
    tl_hdx = download_hdx('timor-leste', cache_dir=cache_dir)
    assert tl_hdx is mock_zipped_file 


def test_get_hdx(tmpdir, mocker):
    mocker.patch('povertymapping.hdx.get_iso3_code', return_value='TLS')
    mock_resource = dict(
        name='tls_general_2020_geotiff.zip',
        download_url='https://example.com/tls_general_2020_geotiff.zip'
    )  
    mock_resources = [mock_resource] 

    mock_dataset = mocker.MagicMock()
    mock_dataset.get_resources = mocker.MagicMock(return_value=mock_resources)
    mocker.patch('hdx.data.dataset.Dataset.read_from_hdx', return_value=mock_dataset)
    mock_zipped_file = mocker.MagicMock()
    mocker.patch('povertymapping.hdx.urlretrieve', return_value=(mock_zipped_file,None,None))
    mock_zipped_object = mocker.MagicMock()
    def create_unzipped_file(unzip_folder):
        with open(unzip_folder/'tls_general_2020.tif','w') as f:
            f.write('')
    mock_zipped_object.extractall = create_unzipped_file # create zipped file
    mock_context_object = mocker.MagicMock()
    mock_context_object.__enter__  = mocker.MagicMock(return_value=mock_zipped_object)
    mocker.patch('povertymapping.hdx.ZipFile', return_value=mock_context_object)
    cache_dir = str(tmpdir/'this-directory-does-not-exist')

    tl_hdx = get_hdx_file('timor-leste', cache_dir=cache_dir)

    assert tl_hdx.exists()
    assert tl_hdx.name == 'tls_general_2020.tif'
    assert tl_hdx.parent.name == 'hdx'
    assert str(tl_hdx.parent.parent) == cache_dir
