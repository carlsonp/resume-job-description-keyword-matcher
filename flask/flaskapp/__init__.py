from pathlib import Path
import string
import spacy
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

            # remove: carriage returns \r, new lines \n
            for replaceme in ['\r', '\n']:
                resume = resume.replace(replaceme, ' ')
                job = job.replace(replaceme, ' ')

            nlp = spacy.load("en_core_web_lg")

            # remove common stop words and run lemmatization

            resume_cleaned = []
            resume_cleaned_lemmatization = []
            for token in nlp(resume):
                if not token.is_stop and token.text not in [" ", "-", "–", "”", "“"] and token.text not in resume_cleaned:
                    resume_cleaned.append(token.text)
                    resume_cleaned_lemmatization.append(token.lemma_)

            job_cleaned = []
            job_cleaned_lemmatization = []
            for token in nlp(job):
                if not token.is_stop and token.text not in [" ", "-", "–", "”", "“"] and token.text not in job_cleaned:
                    job_cleaned.append(token.text)
                    job_cleaned_lemmatization.append(token.lemma_)

            number_matches = 0
            matches = []
            for keyword in job_cleaned_lemmatization:
                if keyword in resume_cleaned_lemmatization:
                    matches.append(keyword)
                    number_matches += 1

            if len(job_cleaned) > 0:
                alignment_percentage = round((number_matches/len(job_cleaned_lemmatization))*100, 2)
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

            return render_template("results.html",
                                   original_resume=request.form.get("resume", ""),
                                   original_job=request.form.get("job", ""),
                                   resume_cleaned=resume_cleaned,
                                   resume_cleaned_lemmatization=resume_cleaned_lemmatization,
                                   job_cleaned=job_cleaned,
                                   job_cleaned_lemmatization=job_cleaned_lemmatization,
                                   number_matches=number_matches,
                                   alignment_percentage=alignment_percentage,
                                   matches=matches,
                                   misalignment=misalignment
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
