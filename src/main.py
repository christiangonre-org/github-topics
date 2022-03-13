from configparser import NoSectionError
import requests
import json
import logging
import os
import re


def setup_logger():
    """
    Setup logger default configuration
    """
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )


def specify_github_url_name(user_name, org_name):
    """
    Returns a full URL with the given USER_NAME or ORG_NAME variable.

    This function checks the USER_NAME or ORG_NAME variables given
    and check conflicts
    """
    # Check that both variables aren´t empty at the same time
    if user_name is None and org_name is None:
        logging.error("USER_NAME org ORG_NAME must be filled")
        exit(1)
    # Check that both variables aren´t filled
    if user_name is not None and org_name is not None:
        logging.error(
            "Only USER_NAME or ORG_NAME can be provided, not both at the same time"
        )
        exit(1)
    if user_name is not None:
        return "https://api.github.com/users/{}/repos".format(user_name)
    if org_name is not NoSectionError:
        return "https://api.github.com/orgs/{}/repos".format(org_name)


def get_repos_topics(url, list_untagged_repos):
    """
    Returns a JSON with all the repositores values

    Filter the repositories with their topics assigned.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(url, headers=headers)

    logging.debug(
        "This is the response code from Github request: %s".format(response.status_code)
    )

    if list_untagged_repos == "true":
        for repo in json.loads(response.content):
            if repo.get("topics") == []:
                logging.info("Repo without topics asigned: {}".format(repo.get("name")))

    return response.content


def get_repos_with_topics(repos):
    """
    Returns a JSON list with repos with topics
    """
    repos_json = {}

    for repo in json.loads(repos):
        if repo.get("topics") != []:
            repos_json[repo.get("name")] = repo.get("topics")

    logging.debug("This is the JSON generated")
    logging.debug(repos_json)

    return repos_json


def get_repos_with_regex(repos, list_topics):
    """
    Returns a JSON list with repos and topic filtered using a list of necessary topics
    """
    repos_json = {}
    topics_regex = re.compile(".*({}).*".format("|".join(list_topics)))

    for repo in json.loads(repos):
        if repo.get("topics") != []:
            logging.info(repo.get("topics"))
            if re.match(topics_regex, ",".join(repo.get("topics"))):
                repos_json[repo.get("name")] = repo.get("topics")

    logging.debug("This is the JSON generated")
    logging.debug(repos_json)

    return repos_json


def clean_brackets_content(init_template_comment, end_template_comment, file_name):
    """
    Clean the content between the comments given in the filename selected
    """
    # Check the lines of the given init_template_comment and end_template_comment variables
    with open(file_name, "r") as myFile:
        for num, line in enumerate(myFile):
            if init_template_comment in line:
                logging.debug("Init template comment found at line: {}".format(num))
                init_template_line = num
            if end_template_comment in line:
                logging.debug("End template comment found at line: {}".format(num))
                end_template_line = num
                break
    myFile.close()

    # Check if the comment werent specified
    try:
        if init_template_line is None or end_template_line is None:
            exit(1)
    except UnboundLocalError:
        logging.error("No INIT_TEMPLATE_COMMENT or END_TEMPLATE_COMMENT were found")
        exit(1)

    # Read an store all lines into list
    with open(file_name, "r") as myFile:
        lines = myFile.readlines()
    myFile.close()

    # Write in the same file all the lines that weren´t inside the comments specified
    # This clean all the content between both comments
    with open(file_name, "w") as myFile:
        for num, line in enumerate(lines):
            if num <= init_template_line or num >= end_template_line:
                myFile.write(line)
    myFile.close()


def write_markdown(init_template_comment, repo_topics, file_name):
    """
    Write all the JSON content as a table inside the file_name given
    """

    # Create a list of lines of the given file_name
    with open(file_name, "r") as f:
        in_file = f.readlines()  # in_file is now a list of lines

    # Create a temporal file
    out_file = []
    for line in in_file:
        out_file.append(line)  # Copy each line, one by one
        if init_template_comment in line:  # Add a new entry after a match
            out_file.append("Repository|Topics\n")
            out_file.append("---|---\n")
            for (
                repo,
                topics,
            ) in repo_topics:  # Generate the table content from the given JSON
                out_file.append("{}|{}\n".format(repo, ",".join(topics)))

    # Overwrite the original file_name with the new content
    with open(file_name, "w") as f:
        f.writelines(out_file)

    logging.info("Markdown write succesfully")


if __name__ == "__main__":

    # Setup logger and variables
    setup_logger()
    init_template_comment = os.environ.get(
        "INIT_TEMPLATE_COMMENT", "<!-- BEGIN_DOCS -->"
    )
    end_template_comment = os.environ.get("END_TEMPLATE_COMMENT", "<!-- END_DOCS -->")
    file_name = os.environ.get("FILE_NAME", "README.md")
    user_name = os.environ.get("USER_NAME")
    org_name = os.environ.get("ORG_NAME", "GoogleContainerTools")
    list_untagged_repos = os.environ.get("LIST_UNTAGGED_REPOS", "false")
    topics_list = json.loads(
        os.environ.get("TOPICS_LIST")
    )  # Convert given env variable to python list

    url_target = specify_github_url_name(user_name=user_name, org_name=org_name)
    repos = get_repos_topics(url=url_target, list_untagged_repos=list_untagged_repos)

    # Check if the user provided a topics list to filter the repos output
    if topics_list is None:
        repo_topics = get_repos_with_topics(repos=repos)
    else:
        repo_topics = get_repos_with_regex(repos=repos, list_topics=topics_list)

    clean_brackets_content(
        init_template_comment=init_template_comment,
        end_template_comment=end_template_comment,
        file_name=file_name,
    )
    write_markdown(
        init_template_comment=init_template_comment,
        repo_topics=repo_topics.items(),
        file_name=file_name,
    )
