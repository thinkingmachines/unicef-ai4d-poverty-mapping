import papermill as pm
import os
import yaml
from datetime import datetime
from PyInquirer.prompt import prompt
from PyInquirer import print_json
import povertymapping.iso3 as iso3 

RUN_CODE = True
DEBUG = True


def exec_pm(*args, **kwargs):
    debug = kwargs.pop("debug", False)
    if debug:
        print_json(dict(where="exec_pm"))
        print_json(dict(environ=dict(EOG_USER=os.environ.get('EOG_USER',None), EOG_PASSWORD=os.environ.get('EOG_PASSWORD',None))))
        print_json(dict(args=args))
        print_json(dict(kwargs=kwargs))
        return None
    return pm.execute_notebook(*args, **kwargs)

def override_defaults(questions, answers, update_list):
    for name in update_list:
        question = next(
            (q for q in questions if q["name"] == name), None
        )
        if question:
            question["default"] = answers[name]

def main():
    if not RUN_CODE:
        print("Hello, run rollout world!")
        return

    print("Answer the following questions")

    with open("scripts/config.yaml") as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
    with open("scripts/config_rollout.yaml") as f:
        config_rollout = yaml.load(f, Loader=yaml.SafeLoader)

    answers = dict(
        eog_user_id="",
        eog_password="",
        country_name="",
        rollout_date="",
        country_code="",
        model_weights_url="",
        country_osm="",
        ookla_year = "",
        nightlights_year = "",
    )
    # prompt for eog_user
    # prompt for eog_password # password
    # prompt for country
    # prompt for rollout_date
    questions1 = config_rollout.get("questions-part1")
    # override defaults
    rollout_date_question = next(
        (q for q in questions1 if q["name"] == "rollout_date"), None
    )
    if rollout_date_question:
        rollout_date_question["default"] = datetime.now().strftime("%Y-%m-%d")

    # print_json(dict(questions=questions))
    answers = prompt(questions1, answers=answers)
    # print_json(dict(answers=answers))

    single_country_models = config.get("single_country_models",[])
    default_config = next((c for c in single_country_models if c["name"] == answers["country_name"]), None)
    cross_country_config = config.get("cross_country_model",None)

    if default_config:
        answers["country_code"] = default_config.get("country_code", "")
        answers["country_osm"] = default_config.get("country_osm", "")
        answers["model_weights_url"] = default_config.get("model_weights_url", "")
        answers["ookla_year"] = default_config.get("ookla_year", "")
        answers["nightlights_year"] = default_config.get("nightlights_year", "")
        model_type = "single-country"
    else:
        model_type = "cross-country"
        answers["country_code"] = iso3.get_iso3_code(answers["country_name"])
        answers["country_osm"] = answers["country_name"]
        if cross_country_config:
            answers["model_weights_url"] = cross_country_config.get("model_weights_url", "")

    print(f"Model type: {model_type}")
    # prompt for country-code, country-osm, model-gdrive-url, nightlights-year, ookla-year
    questions2 = config_rollout.get("questions-part2")
    override_defaults(questions2, answers, ["country_code", "country_osm", "model_weights_url", "nightlights_year", "ookla_year"])
    answers = prompt(questions2, answers=answers)

    os.environ["EOG_USER"] = answers["eog_user_id"]
    os.environ["EOG_PASSWORD"] = answers["eog_password"]
    stages = ["2_generate_grids", "3_rollout_model"]
    stage_params = {
        "2_generate_grids": dict(
            COUNTRY_CODE=answers["country_code"],
            ROLLOUT_DATE=answers["rollout_date"],
        ),
        "3_rollout_model": dict(
            COUNTRY_CODE=answers["country_code"],
            ROLLOUT_DATE=answers["rollout_date"],
            COUNTRY_OSM=answers["country_osm"],
            OOKLA_YEAR=answers["ookla_year"],
            NIGHTLIGHTS_YEAR=answers["nightlights_year"],
            MODEL_WEIGHTS_URL=answers["model_weights_url"],
        ),
    }

    input_notebook_dir = f"notebooks/{model_type}"
    if model_type == "cross-country" and answers["country_code"] == "id": 
        # special case indonesia due to grid size
        input_notebook_dir = "notebooks/cross_country/id"

    output_notebook_dir = f"output-notebooks/{model_type}"
    # execute
    for stage in stages:
        output_stage = f"{answers['country_code']}_{stage}"
        exec_pm(
            f"{input_notebook_dir}/{stage}.ipynb",
            f"{output_notebook_dir}/{output_stage}.ipynb",
            parameters=stage_params[stage],
            debug=DEBUG,
        )


if __name__ == "__main__":
    main()
