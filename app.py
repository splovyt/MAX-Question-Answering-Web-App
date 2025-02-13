from flask import Flask, render_template, request, jsonify
from chatbot import *  # functions for each state
import json
import random

app = Flask(__name__)

# state that the conversation with the chatbot is in
states = {
    1: get_topic,
    2: match,
    3: narrow,
    4: ask,
    5: end
}

textbook_data = None
titles = None
model_endpoint = "http://0.0.0.0:5000/model/predict"


#
# Copyright 2018-2019 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# flattens textbook data for searching and matching user input to sections of the textbook
def flattened_titles(data):
    titles = {}
    for chapter in data:
        titles[(chapter,)] = ("chapter",)
        for section in data[chapter]:
            titles[(chapter, section)] = ("section",)
            for sub in data[chapter][section]:
                titles[(chapter, section, sub)] = ("subsection", data[chapter][section][sub])

    return titles


# used to narrow down the titles among which user input is matching after they have already
# selected a chapter/section
def get_subtitles(data, titles, title):
    raw_title = title[0]  # for searching textbook data, keys are strings not tuples
    if titles[title][0] == "chapter":
        final = {}
        for section in data[raw_title]:
            final[(raw_title, section)] = titles[(raw_title, section)]
            for sub in data[raw_title][section]:
                final[(raw_title, section, sub)] = titles[(raw_title, section, sub)]
        final[title] = titles[title]
        return final
    else:
        final = {}
        for sub in data[title[0]][title[1]]:
            final[(title[0], title[1], sub)] = titles[(title[0], title[1], sub)]
        final[title] = titles[title]
        return final


@app.route("/", methods=["POST", "GET"])
def chat():
    if request.method == "POST":
        data = json.loads(request.data)
        input_text = data["input"]
        state = int(data["state"])
        # gets name of the next function based on state that conversation with chatbot is in
        get_next_text = states.get(state)
        narrowed_titles = titles
        # narrow titles if necessary
        if state == 3:
            narrowed_titles = get_subtitles(textbook_data, titles, choice())

        response, new_state, matches = get_next_text(model_endpoint, input_text, narrowed_titles)
        return jsonify({"response": response, "state": new_state, "matches": matches})
    elif request.method == "GET":
        return render_template("index.html", display_text=f"Hi! My name is QnAit and I'm answering Biology questions today.\nTo get started, please provice a topic. For example: {random.choice(['brain', 'blood', 'cells'])}.", state=1)

if __name__ == "__main__":
    with open("txt.json", "r") as file:
        textbook_data = json.load(file)
    titles = flattened_titles(textbook_data)
    app.run(port=8000, host="0.0.0.0")
