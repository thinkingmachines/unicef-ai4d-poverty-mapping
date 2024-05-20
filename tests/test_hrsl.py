from povertymapping.hrsl import download_hrsl, get_hrsl_file
from pathlib import Path

def test_download_hrsl(tmpdir, mocker):
    mocker.patch('povertymapping.hrsl.get_iso3_code', return_value='TLS')
    mock_resource = dict(
        name='tls_general_2020_geotiff.zip',
        download_url='https://example.com/tls_general_2020_geotiff.zip'
    )  
    mock_resources = [mock_resource] 

    mock_dataset = mocker.MagicMock()
    mock_dataset.get_resources = mocker.MagicMock(return_value=mock_resources)
    mocker.patch('hdx.data.dataset.Dataset.read_from_hdx', return_value=mock_dataset)
    mock_zipped_file = mocker.MagicMock()
    mocker.patch('povertymapping.hrsl.urlretrieve', return_value=(mock_zipped_file,None,None))
    cache_dir = str(tmpdir/'this-directory-does-not-exist')
    tl_hrsl = download_hrsl('timor-leste', cache_dir=cache_dir)
    assert tl_hrsl is mock_zipped_file 


def test_get_hrsl(tmpdir, mocker):
    mocker.patch('povertymapping.hrsl.get_iso3_code', return_value='TLS')
    mock_resource = dict(
        name='tls_general_2020_geotiff.zip',
        download_url='https://example.com/tls_general_2020_geotiff.zip'
    )  
    mock_resources = [mock_resource] 

    mock_dataset = mocker.MagicMock()
    mock_dataset.get_resources = mocker.MagicMock(return_value=mock_resources)
    mocker.patch('hdx.data.dataset.Dataset.read_from_hdx', return_value=mock_dataset)
    mock_zipped_file = mocker.MagicMock()
    mocker.patch('povertymapping.hrsl.urlretrieve', return_value=(mock_zipped_file,None,None))
    mock_zipped_object = mocker.MagicMock()
    def create_unzipped_file(unzip_folder):
        with open(unzip_folder/'tls_general_2020.tif','w') as f:
            f.write('')
    mock_zipped_object.extractall = create_unzipped_file # create zipped file
    mock_context_object = mocker.MagicMock()
    mock_context_object.__enter__  = mocker.MagicMock(return_value=mock_zipped_object)
    mocker.patch('povertymapping.hrsl.ZipFile', return_value=mock_context_object)
    cache_dir = str(tmpdir/'this-directory-does-not-exist')

    tl_hrsl = get_hrsl_file('timor-leste', cache_dir=cache_dir)

    assert tl_hrsl.exists()
    assert tl_hrsl.name == 'tls_general_2020.tif'
    assert tl_hrsl.parent.name == 'hrsl'
    assert str(tl_hrsl.parent.parent) == cache_dir
