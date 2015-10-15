from application import app, db
import os

from flask import Flask, render_template, request, abort, redirect, url_for, flash
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required
from application.models import User
from application.forms import RegistrationForm, ProgrammeForm, ProjectForm, SprintForm
import requests
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
import hashlib
from datetime import date, timedelta

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

password_salt = app.config['SALT'].encode('utf-8')

@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(id=user_id)
    if user.count() == 1:
        return user.one()
    return None

@app.before_first_request
def init_request():
    db.create_all()

#@app.route('/secret')
#@login_required
#def secret():
#    return render_template('secret.html')

@app.route('/logout')
def logout():
    flash('You are now logged out')
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)

    if request.method == 'GET':
        return render_template('register.html', form=form)
    elif request.method == 'POST':
        username = form.username.data
        password = form.password.data.encode('utf-8')

        user = User.query.filter_by(username=username)
        if user.count() == 0:
            user = User(username=username, password=hashlib.sha512(password + password_salt).hexdigest())
            db.session.add(user)
            db.session.commit()

            flash('Welcome {0}. Thank you for registering'.format(username))
            user = User.query.filter_by(username=username).filter_by(password=hashlib.sha512(password + password_salt).hexdigest())
            login_user(user.one())
            try:
                next = request.form['next']
                return redirect(next)
            except:
                return redirect(url_for('index'))
        else:
            flash('The username {0} is already in use.  Please try a new username.'.format(username))
            return redirect(url_for('register'))
    else:
        abort(405)



@app.route('/add_programme', methods=['GET', 'POST'])
@login_required
def add_programme():
    form = ProgrammeForm(request.form)
    if request.method == 'GET':
        return render_template('add_programme.html', form=form)
    elif request.method == 'POST':
        programme_name = form.programme_name.data
        programme_manager = form.programme_manager.data
        service_manager = form.service_manager.data
        response = requests.get(app.config['SCRUM_API'] + '/get/programmes')
        data = response.json()
        if not any(d['name'] == programme_name for d in data):
            payload = {"programme_name":programme_name,"programme_manager":programme_manager, "service_manager": service_manager}
            requests.post(app.config['SCRUM_API'] + '/add/programme', data=json.dumps(payload))
            flash('Programme {0} added'.format(programme_name))
            return redirect(url_for('index'))
        else:
            flash('Programme {0} already exists'.format(programme_name))
            return render_template('add_programme.html', form=form)
        #print(data)
        #return str(data)


@app.route('/add_project/<programme_id>', methods=['GET', 'POST'])
@login_required
def add_project(programme_id):

    response = requests.get(app.config['SCRUM_API'] + '/get/programme/{0}'.format(programme_id))
    programme_data = response.json()
    form = ProjectForm(request.form)
    if request.method == 'GET':
        return render_template('add_project.html', form=form, programme_data=programme_data)
    elif request.method == 'POST':
        project_name = form.project_name.data
        product_owner = form.product_owner.data
        scrum_master = form.scrum_master.data
        project_description = form.project_description.data
        if not any(d['name'] == project_name for d in programme_data['projects']):
            payload = {"project_name":project_name, "programme_id": programme_id, "product_owner": product_owner, "scrum_master": scrum_master, "project_description": project_description}
            requests.post(app.config['SCRUM_API'] + '/add/project', data=json.dumps(payload))
            flash('Project {0} added'.format(project_name))
            return redirect(url_for('index'))
        else:
            flash('Project {0} already exists in {1}'.format(programme_name, programme_data.name))
        return render_template('add_project.html', form=form, programme_data=programme_data)
        #print(data)
        #return str(data)

@app.route('/project/<project_id>', methods=['GET'])
def project(project_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id))
    project_data = response.json()

    velocity_key = []
    velocity_value = []
    for d in project_data['sprint_array']:
        velocity_key.append(str(d['sprint_number']))
        velocity_value.append(str(d['delivered_points']))

    return render_template('project.html', project_data=project_data, velocity_key=','.join(velocity_key), velocity_value=','.join(velocity_value))



@app.route('/project/<project_id>/add_sprint', methods=['GET', 'POST'])
@login_required
def add_sprint(project_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id))
    project_data = response.json()
    form = SprintForm(request.form)
    if request.method == 'GET':

        if project_data['last_sprint_id'] != '':
            response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, project_data['last_sprint_id']))
            sprint_data = response.json()
            form.sprint_number.data = int(sprint_data['sprint_number']) + 1
            form.sprint_days.data = str(sprint_data['sprint_days'])
            form.end_date.data = datetime.strptime(sprint_data['end_date'], '%Y-%m-%d') + timedelta(days=(sprint_data['sprint_days'] + ((sprint_data['sprint_days'] /5) * 2)))
            form.start_date.data = datetime.strptime(sprint_data['start_date'], '%Y-%m-%d') + timedelta(days=(sprint_data['sprint_days'] + ((sprint_data['sprint_days'] /5) * 2)))
            form.sprint_rag.data = sprint_data['sprint_rag']
            form.sprint_risks.data = sprint_data['sprint_risks']
            form.sprint_issues.data = sprint_data['sprint_issues']
            form.sprint_dependencies.data = sprint_data['sprint_dependencies']

        return render_template('add_sprint.html', form=form, project_data=project_data)
    else:
        sprint_number = form.sprint_number.data
        sprint_goal = form.sprint_goal.data
        sprint_days = form.sprint_days.data
        agreed_points = form.agreed_points.data
        start_date = str(form.start_date.data)
        end_date = str(form.end_date.data)
        sprint_rag = form.sprint_rag.data
        sprint_risks = form.sprint_risks.data
        sprint_issues = form.sprint_issues.data
        sprint_dependencies = form.sprint_dependencies.data

        if form.validate_on_submit():
            if not any(d['sprint_number'] == str(sprint_number) for d in project_data['sprint_array']):
                payload = {"project_id": project_id, "start_date": start_date, "end_date": end_date, "sprint_number": sprint_number, "sprint_rag": sprint_rag, "sprint_goal": sprint_goal, "sprint_deliverables": "", "sprint_challenges": "", "agreed_points": agreed_points, "delivered_points": "0", "started_points": "0", "sprint_issues": sprint_issues, "sprint_risks": sprint_risks, "sprint_dependencies": sprint_dependencies, "sprint_days": sprint_days  }
                response = requests.post(app.config['SCRUM_API'] + '/add/sprint', data=json.dumps(payload))
                sprint_data = response.json()

                print(sprint_data)

                sprint_days_array = []
                for i in range(1, (int(sprint_days) + 1)):
                    sprint_days_array.append({"sprint_day": str(i), "sprint_done": "0"})

                payload = {"sprint_id": str(sprint_data['id']), "sprint_days": sprint_days_array}
                requests.post(app.config['SCRUM_API'] + '/update/burn_down', data=json.dumps(payload))

                flash('Add Sprint {0} for {1}'.format(sprint_number, project_data['name']))
                return redirect(url_for('project', project_id=project_id))
            else:
                flash('Sprint {0} already exists in {1}'.format(sprint_number, project_data['name']))


        return render_template('add_sprint.html', form=form, project_data=project_data)


@app.route('/project/<project_id>/<sprint_id>', methods=['GET', 'POST'])
def sprint(project_id, sprint_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    points_per_day = sprint_data['agreed_points'] / sprint_data['sprint_days']

    sprint_days_array = []
    sprint_days_burndown = []
    sprint_days_burndown_expected = []

    total_points = sprint_data['agreed_points']
    total_points_expected = sprint_data['agreed_points']

    for d in sprint_data['burndown']:
        sprint_days_array.append(str(d['sprint_day']))
        total_points = total_points - int(d['sprint_done'])
        sprint_days_burndown.append(str(total_points))
        total_points_expected = total_points_expected - points_per_day

        sprint_days_burndown_expected.append(str(round(total_points_expected)))


    return render_template('sprint.html', sprint_data=sprint_data, project_data=project_data, sprint_days_burndown=','.join(sprint_days_burndown), sprint_days_array=','.join(sprint_days_array), sprint_days_burndown_expected=','.join(sprint_days_burndown_expected))


@app.route('/project/<project_id>/<sprint_id>/burndown', methods=['GET', 'POST'])
def view_burndown(project_id, sprint_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    points_per_day = sprint_data['agreed_points'] / sprint_data['sprint_days']

    sprint_days_array = []
    sprint_days_burndown = []
    sprint_days_burndown_expected = []

    total_points = sprint_data['agreed_points']
    total_points_expected = sprint_data['agreed_points']

    for d in sprint_data['burndown']:
        sprint_days_array.append(str(d['sprint_day']))
        total_points = total_points - int(d['sprint_done'])
        sprint_days_burndown.append(str(total_points))
        total_points_expected = total_points_expected - points_per_day

        sprint_days_burndown_expected.append(str(round(total_points_expected)))


    return render_template('burndown.html', sprint_data=sprint_data, project_data=project_data, sprint_days_burndown=','.join(sprint_days_burndown), sprint_days_array=','.join(sprint_days_array), sprint_days_burndown_expected=','.join(sprint_days_burndown_expected))


@app.route('/project/<project_id>/edit_sprint/<sprint_id>', methods=['GET', 'POST'])
@login_required
def edit_sprint(project_id, sprint_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    form = SprintForm(request.form)
    form.sprint_days.data = str(sprint_data['sprint_days'])
    form.delivered_points.data = sprint_data['delivered_points']

    if request.method == 'GET':
        form.sprint_number.data = sprint_data['sprint_number']
        form.agreed_points.data = sprint_data['agreed_points']
        form.sprint_deliverables.data = sprint_data['sprint_deliverables']
        form.started_points.data = sprint_data['started_points']
        form.sprint_dependencies.data = sprint_data['sprint_dependencies']
        form.end_date.data = datetime.strptime(sprint_data['end_date'], '%Y-%m-%d')
        form.start_date.data = datetime.strptime(sprint_data['start_date'], '%Y-%m-%d')
        form.sprint_risks.data = sprint_data['sprint_risks']
        form.sprint_goal.data = sprint_data['sprint_goal']
        form.sprint_rag.data = sprint_data['sprint_rag']
        form.sprint_challenges.data = sprint_data['sprint_challenges']
        form.sprint_issues.data = sprint_data['sprint_issues']

        return render_template('edit_sprint.html', project_data=project_data, sprint_data=sprint_data, form=form)
    else:
        if form.validate_on_submit():

            sprint_num_found = False;
            for d in project_data['sprint_array']:
                if d['sprint_number'] == form.sprint_number.data:
                    if str(d['id']) != sprint_id:
                        sprint_num_found = True

            if sprint_num_found == False:
                payload = {"project_id":project_id, "sprint_days": form.sprint_days.data, "start_date": str(form.start_date.data), "end_date": str(form.end_date.data), "sprint_number": form.sprint_number.data, "sprint_rag": form.sprint_rag.data, "sprint_goal": form.sprint_goal.data, "sprint_deliverables": form.sprint_deliverables.data, "sprint_challenges": form.sprint_challenges.data, "agreed_points": form.agreed_points.data, "delivered_points": sprint_data['delivered_points'], "started_points": form.started_points.data, "sprint_issues": form.sprint_issues.data, "sprint_risks": form.sprint_risks.data, "sprint_dependencies": form.sprint_dependencies.data  }
                requests.post(app.config['SCRUM_API'] + '/update/sprint/{0}'.format(sprint_id), data=json.dumps(payload))
                sprint_data = response.json()

                flash('Sprint Updated')
                return redirect(url_for('sprint', project_id=project_id, sprint_id=sprint_id))
            else:
                flash('That Sprint Number is already used elsewhere')
        else:
            flash('There was an error, please review')
    return render_template('edit_sprint.html', project_data=project_data, sprint_data=sprint_data, form=form)

@app.route('/edit_project/<project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/programme/{0}'.format(project_data['programme_id']))
    programme_data = response.json()

    form = ProjectForm(request.form)
    if request.method == 'GET':
        form.project_name.data = project_data['name']
        form.product_owner.data = project_data['product_owner']
        form.scrum_master.data = project_data['scrum_master']
        form.project_description.data = project_data['project_description']

        return render_template('edit_project.html', project_data=project_data, form=form)
    else:
        if form.validate_on_submit():

            project_name_found = False;

            for d in programme_data['projects']:
                if d['name'] == form.project_name.data:
                    if str(d['id']) != project_id:
                        project_name_found = True

            if project_name_found == False:
                payload = {"project_name":form.project_name.data, "programme_id": project_data['programme_id'], "product_owner": form.product_owner.data, "scrum_master": form.scrum_master.data, "project_description": form.project_description.data}
                requests.post(app.config['SCRUM_API'] + '/update/project/{0}'.format(project_id), data=json.dumps(payload))

                flash('Project Updated')
                return redirect(url_for('project', project_id=project_id))
            else:
                flash('A project of the same name already exists')
        else:
            flash('There was an error, please review')
        return render_template('edit_project.html', project_data=project_data, form=form)

@app.route('/edit_programme/<programme_id>', methods=['GET', 'POST'])
@login_required
def edit_programme(programme_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/programme/{0}'.format(programme_id))
    programme_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/programmes')
    data = response.json()

    form = ProgrammeForm(request.form)
    if request.method == 'GET':
        form.programme_name.data = programme_data['name']
        form.programme_manager.data = programme_data['programme_manager']
        form.service_manager.data = programme_data['service_manager']

        return render_template('edit_programme.html', programme_data=programme_data, form=form)
    else:
        if form.validate_on_submit():

            programme_name_found = False;

            for d in data:
                if d['name'] == form.programme_name.data:
                    if str(d['id']) != programme_id:
                        programme_name_found = True

            if programme_name_found == False:
                payload = {"programme_name":form.programme_name.data,"programme_manager":form.programme_manager.data, "service_manager": form.programme_manager.data}
                requests.post(app.config['SCRUM_API'] + '/update/programme/{0}'.format(programme_id), data=json.dumps(payload))

                flash('Programme Updated')
                return redirect(url_for('programme', programme_id=programme_id))
            else:
                flash('A programme of the same name already exists')
        else:
            flash('There was an error, please review')
        return render_template('edit_programme.html', programme_data=programme_data, form=form)


@app.route('/project/<project_id>/edit_sprint/<sprint_id>/burndown', methods=['GET', 'POST'])
@login_required
def burndown(project_id, sprint_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    if request.method == 'GET':
        return render_template('edit_burndown.html', project_data=project_data, sprint_data=sprint_data)
    else:
        sprintdays = request.form.getlist('sprintday')
        pointsdones = request.form.getlist('pointsdone')
        points_done = 0
        sprint_days_array = []
        for i in range(0, len(sprintdays)):
            points_done = points_done + int(pointsdones[i])
            sprint_days_array.append({"sprint_day": sprintdays[i], "sprint_done": pointsdones[i]})

        payload = {"sprint_id": str(sprint_id), "sprint_days": sprint_days_array}
        requests.post(app.config['SCRUM_API'] + '/update/burn_down', data=json.dumps(payload))

        payload = {"project_id":sprint_data['project_id'], "sprint_days": sprint_data['sprint_days'], "start_date": sprint_data['start_date'], "end_date": sprint_data['end_date'], "sprint_number": sprint_data['sprint_number'], "sprint_rag": sprint_data['sprint_rag'], "sprint_goal": sprint_data['sprint_goal'], "sprint_deliverables": sprint_data['sprint_deliverables'], "sprint_challenges": sprint_data['sprint_challenges'], "agreed_points": sprint_data['agreed_points'], "delivered_points": str(points_done), "started_points": sprint_data['started_points'], "sprint_issues": sprint_data['sprint_issues'], "sprint_risks": sprint_data['sprint_risks'], "sprint_dependencies": sprint_data['sprint_dependencies']  }
        requests.post(app.config['SCRUM_API'] + '/update/sprint/{0}'.format(sprint_id), data=json.dumps(payload))

        flash('Burndown Updated')
        return redirect(url_for('sprint', project_id=project_id, sprint_id=sprint_id))


@app.route('/delete/sprint/<project_id>/<sprint_id>', methods=['GET', 'POST'])
@login_required
def delete_sprint(project_id, sprint_id):
    response = requests.get(app.config['SCRUM_API'] + '/delete/sprint/{0}'.format(sprint_id))
    return redirect(url_for('project', project_id=project_id))


@app.route('/delete/project/<project_id>', methods=['GET', 'POST'])
@login_required
def delete_project(project_id):
    response = requests.get(app.config['SCRUM_API'] + '/delete/project/{0}'.format(project_id))
    return redirect(url_for('index'))

@app.route('/delete/programme/<programme_id>', methods=['GET', 'POST'])
@login_required
def delete_programme(programme_id):
    response = requests.get(app.config['SCRUM_API'] + '/delete/programme/{0}'.format(programme_id))
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():

    form = RegistrationForm(request.form)

    if request.method == 'GET':
        return render_template('login.html', next=request.args.get('next'), form=form)
    elif request.method == 'POST':
        username = form.username.data
        password = form.password.data.encode('utf-8')

        user = User.query.filter_by(username=username).filter_by(password=hashlib.sha512(password + password_salt).hexdigest())
        if user.count() == 1:
            login_user(user.one())
            flash('Welcome back {0}'.format(username))
            try:
                next = request.form['next']
                return redirect(next)
            except:
                return redirect(url_for('index'))
        else:
            flash('Invalid login')
            return redirect(url_for('login'))
    else:
        return abort(405)

@app.route('/')
def index():
    response = requests.get(app.config['SCRUM_API'] + '/get/programmes')
    data = response.json()
    return render_template('index.html', data=data)


@app.route('/programme/<programme_id>')
def programme(programme_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/programme/{0}'.format(programme_id))
    data = response.json()
    return render_template('programme.html', data=data)
