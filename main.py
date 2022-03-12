import requests
import json
import logging
import os


def setup_logger():
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"),
        format='%(asctime)s:%(levelname)s:%(message)s'
        )


def get_repos_topics(url):
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }

    response = requests.get(url, headers=headers)

    logging.debug("This is the response code from Github request: {}".format(response.status_code))
    repos_json = {}
    for repo in json.loads(response.content):
        if repo.get("topics") != []:
            repos_json[repo.get("name")] = repo.get("topics")

    logging.debug("This is the JSON generated")
    return repos_json


def clean_brackets_content(init_sentence, end_sentence, filename):
    with open(filename, "r") as myFile:
        for num, line in enumerate(myFile):
            if init_sentence in line:
                logging.info('Init sentence found at line:', num)
                init_sentence_line = num
            if end_sentence in line:
                logging.info('End sentence found at line:', num)
                end_sentence_line = num
                break
    myFile.close()

    try:
        if init_sentence_line is None or end_sentence_line is None:
            exit(1)
    except UnboundLocalError:
        print("No init sentence or end sentence were found")
        exit(1)

    with open(filename, 'r') as myFile:
        # read an store all lines into list
        lines = myFile.readlines()
    myFile.close()

    with open(filename, "w") as myFile:
        for num, line in enumerate(lines):
            if num <= init_sentence_line or num >= end_sentence_line:
                print(num)
                myFile.write(line)
    myFile.close()


def write_markdown(init_sentence, repo_topics, file_name):

    # Let's read our input file into a variable
    with open(file_name, 'r') as f:
        in_file = f.readlines()  # in_file is now a list of lines

    # Now we start building our output
    out_file = []
    for line in in_file:
        out_file.append(line)  # copy each line, one by one
        if init_sentence in line:  # add a new entry, after a match
            out_file.append('Repository|Topics\n')
            out_file.append('---|---\n')
            for repo, topics in repo_topics:
                out_file.append("{}|{}\n".format(repo, ",".join(topics)))
                print(repo)
                print(topics)

    # Now let's write all those lines to a new output file.
    # You would re-write over the input file now, if you wanted!
    with open(file_name, 'w') as f:
        f.writelines(out_file)


if __name__ == "__main__":
    setup_logger()
    init_template = "<!-- BEGIN_DOCS -->"
    end_template = "<!-- END_DOCS -->"
    filename = "README.md"
    repo_topics = get_repos_topics("https://api.github.com/orgs/GoogleContainerTools/repos")
    clean_brackets_content(init_sentence=init_template, end_sentence=end_template, filename=filename)
    write_markdown(init_sentence=init_template, repo_topics=repo_topics.items(), file_name=filename)
