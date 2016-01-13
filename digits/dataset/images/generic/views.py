# Copyright (c) 2015-2016, NVIDIA CORPORATION.  All rights reserved.
from __future__ import absolute_import

import flask

from .forms import GenericImageDatasetForm
from .job import GenericImageDatasetJob
from digits import utils
from digits.dataset import tasks
from digits.webapp import app, scheduler
from digits.utils.forms import fill_form_if_cloned, save_form_to_job
from digits.utils.routing import request_wants_json, job_from_request

NAMESPACE = '/datasets/images/generic'

@app.route(NAMESPACE + '/new', methods=['GET'])
@utils.auth.requires_login
def generic_image_dataset_new():
    """
    Returns a form for a new GenericImageDatasetJob
    """
    form = GenericImageDatasetForm()

    ## Is there a request to clone a job with ?clone=<job_id>
    fill_form_if_cloned(form)

    return flask.render_template('datasets/images/generic/new.html', form=form)

@app.route(NAMESPACE + '.json', methods=['POST'])
@app.route(NAMESPACE, methods=['POST'])
@utils.auth.requires_login(redirect=False)
def generic_image_dataset_create():
    """
    Creates a new GenericImageDatasetJob

    Returns JSON when requested: {job_id,name,status} or {errors:[]}
    """
    form = GenericImageDatasetForm()

    ## Is there a request to clone a job with ?clone=<job_id>
    fill_form_if_cloned(form)

    if not form.validate_on_submit():
        if request_wants_json():
            return flask.jsonify({'errors': form.errors}), 400
        else:
            return flask.render_template('datasets/images/generic/new.html', form=form), 400

    job = None
    try:
        job = GenericImageDatasetJob(
                username    = utils.auth.get_username(),
                name        = form.dataset_name.data,
                mean_file   = form.prebuilt_mean_file.data.strip(),
                )

        if form.method.data == 'prebuilt':
            pass
        else:
            raise ValueError('method not supported')

        force_same_shape = form.force_same_shape.data

        job.tasks.append(
                tasks.AnalyzeDbTask(
                    job_dir     = job.dir(),
                    database    = form.prebuilt_train_images.data,
                    purpose     = form.prebuilt_train_images.label.text,
                    force_same_shape = force_same_shape,
                    )
                )

        if form.prebuilt_train_labels.data:
            job.tasks.append(
                    tasks.AnalyzeDbTask(
                        job_dir     = job.dir(),
                        database    = form.prebuilt_train_labels.data,
                        purpose     = form.prebuilt_train_labels.label.text,
                        force_same_shape = force_same_shape,
                        )
                    )

        if form.prebuilt_val_images.data:
            job.tasks.append(
                    tasks.AnalyzeDbTask(
                        job_dir     = job.dir(),
                        database    = form.prebuilt_val_images.data,
                        purpose     = form.prebuilt_val_images.label.text,
                        force_same_shape = force_same_shape,
                        )
                    )
            if form.prebuilt_val_labels.data:
                job.tasks.append(
                        tasks.AnalyzeDbTask(
                            job_dir     = job.dir(),
                            database    = form.prebuilt_val_labels.data,
                            purpose     = form.prebuilt_val_labels.label.text,
                            force_same_shape = force_same_shape,
                            )
                        )

        ## Save form data with the job so we can easily clone it later.
        save_form_to_job(job, form)

        scheduler.add_job(job)

        if request_wants_json():
            return flask.jsonify(job.json_dict())
        else:
            return flask.redirect(flask.url_for('datasets_show', job_id=job.id()))

    except:
        if job:
            scheduler.delete_job(job)
        raise

def show(job):
    """
    Called from digits.dataset.views.datasets_show()
    """
    return flask.render_template('datasets/images/generic/show.html', job=job)

@app.route(NAMESPACE + '/summary', methods=['GET'])
def generic_image_dataset_summary():
    """
    Return a short HTML summary of a DatasetJob
    """
    job = job_from_request()

    return flask.render_template('datasets/images/generic/summary.html', dataset=job)

