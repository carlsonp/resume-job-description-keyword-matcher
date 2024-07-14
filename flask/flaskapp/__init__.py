from pathlib import Path
import string
import spacy
import re
import humanize
from flask_compress import Compress

from flask import Flask, redirect, render_template, request, url_for


def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder="/static/")
    Compress(app)

    @app.route("/")
    def homepage():
        try:
            return render_template("index.html")
        except Exception as e:
            app.logger.error(e)
            return "Failure on homepage"

    @app.route("/compare")
    def compare():
        try:
            return render_template("compare.html")
        except Exception as e:
            app.logger.error(e)
            return "Failure on compare page"
        
    @app.route("/results", methods=["POST"])
    def results():
        try:
            resume = remove_punctuation(request.form.get("resume", "").lower())
            job = remove_punctuation(request.form.get("job", "").lower())

            nlp = spacy.load("en_core_web_lg")

            # remove common stop words and run lemmatization

            resume_cleaned = []
            resume_cleaned_lemmatization = []
            for token in nlp(resume):
                if not token.is_stop and token.text not in resume_cleaned and len(token.text) > 3 and token.pos_ not in ['ADJ', 'ADP', 'ADV', 'AUX', 'DET', 'INTJ', 'NUM', 'PART','PRON', 'PUNCT', 'SCONJ', 'SYM', 'X']:
                    resume_cleaned.append(token.text)
                    resume_cleaned_lemmatization.append(token.lemma_)

            job_cleaned = []
            job_cleaned_lemmatization = []
            for token in nlp(job):
                if not token.is_stop and token.text not in job_cleaned and len(token.text) > 3 and token.pos_ not in ['ADJ', 'ADP', 'ADV', 'AUX', 'DET', 'INTJ', 'NUM', 'PART','PRON',  'PUNCT', 'SCONJ', 'SYM', 'X']:
                    job_cleaned.append(token.text)
                    job_cleaned_lemmatization.append(token.lemma_)

            matches = {}
            for i, keyword in enumerate(job_cleaned_lemmatization):
                if keyword in resume_cleaned_lemmatization:
                    if keyword != job_cleaned[i]:
                        matches[f"{keyword} ({job_cleaned[i]})"] = job.count(job_cleaned[i])
                    else:
                        matches[keyword] = job.count(job_cleaned[i])
            
            # sort matches by count in descending order
            matches = dict(sorted(matches.items(), key=lambda item: item[1], reverse=True))

            if len(job_cleaned) > 0:
                alignment_percentage = round((len(matches)/len(job_cleaned_lemmatization))*100, 2)
            else:
                alignment_percentage = 0

            misalignment = {}
            for i, keyword in enumerate(job_cleaned_lemmatization):
                if keyword not in resume_cleaned_lemmatization:
                    if keyword != job_cleaned[i]:
                        misalignment[f"{keyword} ({job_cleaned[i]})"] = job.count(job_cleaned[i])
                    else:
                        misalignment[keyword] = job.count(job_cleaned[i])

            # sort misalignment by count in descending order
            misalignment = dict(sorted(misalignment.items(), key=lambda item: item[1], reverse=True))

            # generate a colored job description to display to show matches and missing keywords
            colored_job_description = request.form.get("job", "")
            compiled_pattern = re.compile(r'(\w+)\s+\((\w+)\)|(\w+)', re.IGNORECASE)
            for word in matches.keys():
                regex_matches = compiled_pattern.search(word)
                if regex_matches:
                    # look for original word first, then lemmatized (likely shorter word)
                    for match in [item for item in [regex_matches.group(1), regex_matches.group(0), regex_matches.group(2)] if item is not None and item]:
                        # don't search and replace words we're adding for the coloring
                        if match not in ['span', 'class', 'text', 'success', 'danger']:
                            pattern = re.compile(r'\b'+re.escape(match)+r'\b', re.MULTILINE | re.IGNORECASE)
                            colored_job_description = pattern.sub(f"<span class='text-success'>{match}</span>", colored_job_description)
            for word in misalignment.keys():
                regex_matches = compiled_pattern.search(word)
                if regex_matches:
                    # look for original word first, then lemmatized (likely shorter word)
                    for match in [item for item in [regex_matches.group(1), regex_matches.group(0), regex_matches.group(2)] if item is not None]:
                        # don't search and replace words we're adding for the coloring
                        if match not in ['span', 'class', 'text', 'success', 'danger']:
                            pattern = re.compile(r'\b'+re.escape(match)+r'\b', re.MULTILINE | re.IGNORECASE)
                            colored_job_description = pattern.sub(f"<span class='text-danger'>{match}</span>", colored_job_description)
            
            top_keywords_add = []
            # https://www.kaggle.com/datasets/timvdnbroucke/top-500-resume-keywords
            # https://www.colorado.edu/career/job-searching/resumes-and-cover-letters/resumes/action-verbs-use-your-resume
            # parse through popular keywords to see if there are any in the job description we're missing
            with open('resume_keywords_cleaned.txt', 'r') as f:
                for token in nlp(f.read().lower()):
                    if not token.is_stop and token.text not in job_cleaned and len(token.text) > 3 and token.pos_ not in ['ADJ', 'ADP', 'ADV', 'AUX', 'DET', 'INTJ', 'NUM', 'PART','PRON',  'PUNCT', 'SCONJ', 'SYM', 'X']:
                        for possiblematch in [token.text, token.lemma_]:
                            if possiblematch not in matches and possiblematch in misalignment and possiblematch not in top_keywords_add:
                                top_keywords_add.append(possiblematch)

            return render_template("results.html",
                                   original_resume=request.form.get("resume", ""),
                                   original_job=request.form.get("job", ""),
                                   resume_cleaned=resume_cleaned,
                                   resume_cleaned_lemmatization=resume_cleaned_lemmatization,
                                   job_cleaned=job_cleaned,
                                   job_cleaned_lemmatization=job_cleaned_lemmatization,
                                   number_matches=len(matches),
                                   alignment_percentage=alignment_percentage,
                                   matches=matches,
                                   misalignment=misalignment,
                                   misalignment_count=len(misalignment),
                                   colored_job_description=colored_job_description,
                                   top_keywords_add=top_keywords_add
                                   )
        except Exception as e:
            app.logger.error(e)
            return "Failure on results page"

    @app.route("/health")
    def health():
        return "Ok"
    
    def remove_punctuation(text):
        return text.translate(str.maketrans('', '', string.punctuation))

    return app
