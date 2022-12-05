from povertymapping.utils.data_utils import get_dhs_dict

DHS_SAMPLE_DATA_DIR = 'test_data/dhs_sample'

def test_get_dhs_dict():
    dhs_dict = get_dhs_dict(f'{DHS_SAMPLE_DATA_DIR}/TLHR71FL.DO')
    assert dhs_dict is not None