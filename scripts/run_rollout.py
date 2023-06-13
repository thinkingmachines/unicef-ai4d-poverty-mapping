import papermill as pm
import os
import yaml
from datetime import datetime
from PyInquirer.prompt import prompt
from PyInquirer import print_json
from prompt_toolkit.validation import Validator, ValidationError
import povertymapping.iso3 as iso3
import re as regex

RUN_CODE = True
DEBUG = True


def exec_pm(*args, **kwargs):
    debug = kwargs.pop("debug", False)
    if debug:
        print_json(dict(where="exec_pm"))
        print_json(
            dict(
                environ=dict(
                    EOG_USER=os.environ.get("EOG_USER", None),
                    EOG_PASSWORD=os.environ.get("EOG_PASSWORD", None),
                )
            )
        )
        print_json(dict(args=args))
        print_json(dict(kwargs=kwargs))
        # return None
    return pm.execute_notebook(*args, **kwargs)


def override_defaults(questions, answers, update_list):
    for name in update_list:
        question = next((q for q in questions if q["name"] == name), None)
        if question:
            question["default"] = answers[name]


class CountryNameValidator(Validator):
    def validate(self, document):
        ok = iso3.is_valid_country_name(document.text)
        if not ok:
            raise ValidationError(
                message="Enter a valid country name (lower case only)",
                cursor_position=len(document.text),
            )  # Move cursor to end


class RequiredValidator(Validator):
    def validate(self, document):
        ok = len(document.text) > 0
        if not ok:
            raise ValidationError(
                message="Enter a value (required)", cursor_position=len(document.text)
            )  # Move cursor to end


date_pat = r"\d{4}-\d{2}-\d{2}"


class DateFormatValidator(Validator):
    def validate(self, document):
        ok = regex.match(date_pat, document.text)
        if not ok:
            raise ValidationError(
                message="Enter a valid date (yyyy-mm-dd)",
                cursor_position=len(document.text),
            )  # Move cursor to end


year_pat = r"\d{4}"


class YearValidator(Validator):
    def validate(self, document):
        ok = regex.match(year_pat, document.text)
        if not ok:
            raise ValidationError(
                message="Enter a valid year (yyyy)", cursor_position=len(document.text)
            )  # Move cursor to end


url_pat = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
# see https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url


class UrlValidator(Validator):
    def validate(self, document):
        ok = regex.match(url_pat, document.text)
        if not ok:
            raise ValidationError(
                message="Enter a valid url (https://www.example.com)",
                cursor_position=len(document.text),
            )  # Move cursor to end


def prompt_answers(config_rollout, config, answers, use_default=True):
    # prompt for eog_user
    # prompt for eog_password # password
    # prompt for country
    # prompt for rollout_date
    questions1 = config_rollout.get("questions-part1")
    for q in questions1:
        q["validate"] = RequiredValidator

    # override defaults
    if use_default:
        rollout_date_question = next(
            (q for q in questions1 if q["name"] == "rollout_date"), None
        )
        if rollout_date_question:
            rollout_date_question["default"] = datetime.now().strftime("%Y-%m-%d")
            rollout_date_question["validate"] = DateFormatValidator
    else:
        override_defaults(
            questions1,
            answers,
            [
                "rollout_date",
                "country_name",
                "eog_user_id",
                "eog_password",            ],
        )

    country_name_question = next(
        (q for q in questions1 if q["name"] == "country_name"), None
    )
    if country_name_question:
        country_name_question["validate"] = CountryNameValidator
    try:
        answers = prompt(questions1, answers=answers, raise_keyboard_interrupt=True)
    except KeyboardInterrupt as e:
        print("User cancelled input")
        raise e 
    single_country_models = config.get("single_country_models", [])
    cross_country_config = config.get("cross_country_model", None)

    if use_default:
        default_config = next(
            (c for c in single_country_models if c["name"] == answers["country_name"]), None
        )
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
                answers["model_weights_url"] = cross_country_config.get(
                    "model_weights_url", ""
                )
    else:
        model_type = answers['model_type']

    print(f"Model type: {model_type}")
    answers["model_type"] = model_type
    # prompt for country-code, country-osm, model-gdrive-url, nightlights-year, ookla-year
    questions2 = config_rollout.get("questions-part2")
    for q in questions2:
        q["validate"] = RequiredValidator

    model_weights_question = next(
        (q for q in questions2 if q["name"] == "model_weights_url"), None
    )
    if model_weights_question:
        model_weights_question["validate"] = UrlValidator

    years_questions = [
        q for q in questions2 if q["name"] in ["nightlights_year", "ookla_year"]
    ]
    for q in years_questions:
        q["validate"] = YearValidator

    override_defaults(
        questions2,
        answers,
        [
            "country_code",
            "country_osm",
            "model_weights_url",
            "nightlights_year",
            "ookla_year",
        ],
    )
    try:
        answers = prompt(questions2, answers=answers, raise_keyboard_interrupt=True)
    except KeyboardInterrupt as e:
        print("User cancelled input")
        raise e
    return answers


def confirm_answers(answers):
    password = answers["eog_password"]
    enc_pwd = password[0] + '*'* (len(password)-2) + password[-1] 
    confirm_str = f"""
    Your current settings:
    eog_user_id: {answers["eog_user_id"]}
    eog_password: {enc_pwd}
    country_name: {answers["country_name"]}
    rollout_date: {answers["rollout_date"]}
    country_code: {answers["country_code"]}
    model_weights_url: {answers["model_weights_url"]}
    country_osm: {answers["country_osm"]}
    ookla_year: {answers["ookla_year"]}
    nightlights_year: {answers["nightlights_year"]}
    model_type: {answers["model_type"]}
    Are these correct? (Y/n)
    """
    # print(confirm_str)
    confirm_prompt = dict(
        name="confirm_answers", type="confirm", message=confirm_str, default=True
    )
    try:
        confirm_answer = prompt([confirm_prompt],raise_keyboard_interrupt=True)
    except KeyboardInterrupt as e:
        print("User cancelled input")
        raise e
    return confirm_answer["confirm_answers"]


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
        ookla_year="",
        nightlights_year="",
        model_type="",
    )
    confirm = False
    use_default = True
    while not confirm:
        try:
            answers = prompt_answers(config_rollout, config, answers, use_default=use_default)
        except KeyboardInterrupt:
            return
        try:
            confirm = confirm_answers(answers)
        except KeyboardInterrupt:
            return
        use_default = False

    os.environ["EOG_USER"] = answers["eog_user_id"]
    os.environ["EOG_PASSWORD"] = answers["eog_password"]

    model_type = answers["model_type"]
    input_notebook_dir = f"notebooks/{model_type}"
    if model_type == "cross-country" and answers["country_code"] == "id":
        # special case indonesia due to grid size
        input_notebook_dir = "notebooks/cross_country/id"

    output_notebook_dir = f"output-notebooks/{model_type}"

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
