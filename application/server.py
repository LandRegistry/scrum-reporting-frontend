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
from datetime import date, timedelta, time

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
        delivery_manager = form.delivery_manager.data
        scrum_tool_link = form.scrum_tool_link.data
        if not any(d['name'] == project_name for d in programme_data['projects']):
            payload = {"project_name":project_name, "programme_id": programme_id, "product_owner": product_owner, "scrum_master": scrum_master, "project_description": project_description, "delivery_manager": delivery_manager, "scrum_tool_link": scrum_tool_link}
            response = requests.post(app.config['SCRUM_API'] + '/add/project', data=json.dumps(payload))
            project_data = response.json()

            payload = {"project_id": str(project_data['id']), "daytype_status": 'F', 'daytype_name': 'Full Day', 'daytype_day': '1.0', 'daytype_color': '27ae60', 'daytype_order': '1' }

            print(payload)
            requests.post(app.config['SCRUM_API'] + '/add/daytype', data=json.dumps(payload))
            payload = {"project_id": str(project_data['id']), "daytype_status": '1/2', 'daytype_name': 'Half Day', 'daytype_day': '0.5', 'daytype_color': 'f39c12', 'daytype_order': '2' }
            requests.post(app.config['SCRUM_API'] + '/add/daytype', data=json.dumps(payload))
            payload = {"project_id": str(project_data['id']), "daytype_status": 'L', 'daytype_name': 'Leave', 'daytype_day': '0.0', 'daytype_color': 'FFFFFF', 'daytype_order': '3' }
            requests.post(app.config['SCRUM_API'] + '/add/daytype', data=json.dumps(payload))
            payload = {"project_id": str(project_data['id']), "daytype_status": 'Tr', 'daytype_name': 'Training', 'daytype_day': '0.0', 'daytype_color': '9b59b6', 'daytype_order': '4' }
            requests.post(app.config['SCRUM_API'] + '/add/daytype', data=json.dumps(payload))

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

    if project_data['last_sprint_id'] != '':
        response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, project_data['last_sprint_id']))
        previous_sprint_data = response.json()

    if request.method == 'GET':

        if project_data['last_sprint_id'] != '':
            form.sprint_number.data = int(previous_sprint_data['sprint_number']) + 1
            form.sprint_days.data = str(previous_sprint_data['sprint_days'])
            form.end_date.data = datetime.strptime(previous_sprint_data['end_date'], '%Y-%m-%d') + timedelta(days=(previous_sprint_data['sprint_days'] + ((previous_sprint_data['sprint_days'] /5) * 2)))
            form.start_date.data = datetime.strptime(previous_sprint_data['start_date'], '%Y-%m-%d') + timedelta(days=(previous_sprint_data['sprint_days'] + ((previous_sprint_data['sprint_days'] /5) * 2) + 1))
            form.sprint_rag.data = previous_sprint_data['sprint_rag']
            form.sprint_risks.data = previous_sprint_data['sprint_risks']
            form.sprint_issues.data = previous_sprint_data['sprint_issues']
            form.sprint_dependencies.data = previous_sprint_data['sprint_dependencies']

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
                payload = {"project_id": project_id, "start_date": start_date, "end_date": end_date, "sprint_number": sprint_number, "sprint_rag": sprint_rag, "sprint_goal": sprint_goal, "sprint_deliverables": "", "sprint_challenges": "", "agreed_points": agreed_points, "delivered_points": "0", "started_points": "0", "sprint_issues": sprint_issues, "sprint_risks": sprint_risks, "sprint_dependencies": sprint_dependencies, "sprint_days": sprint_days, "sprint_teamdays": 0  }
                response = requests.post(app.config['SCRUM_API'] + '/add/sprint', data=json.dumps(payload))
                sprint_data = response.json()

                print(sprint_data)

                sprint_days_array = []
                for i in range(1, (int(sprint_days) + 1)):
                    sprint_days_array.append({"sprint_day": str(i), "sprint_done": "0"})

                    payload = {"sprint_id": str(sprint_data['id']), "sprint_days": sprint_days_array}
                    requests.post(app.config['SCRUM_API'] + '/update/burn_down', data=json.dumps(payload))

                if project_data['last_sprint_id'] != '':
                    for person in previous_sprint_data['sprintpeople_array']:
                        print(sprint_data['id'])
                        print(person['person_name'] )

                        payload = {"sprint_id":str(sprint_data['id']), "person_name": person['person_name'] }
                        response = requests.post(app.config['SCRUM_API'] + '/add/sprintperson', data=json.dumps(payload))
                        sprintperson_data = response.json()

                        sprintperson_days_array = []
                        for i in range(1, (int(sprint_days) + 1)):
                            sprintperson_days_array.append({"sprint_day": str(i), "sprint_daystatus": "0"})

                        payload = {"sprintpeople_id": str(sprintperson_data['id']), "sprint_days": sprintperson_days_array}
                        requests.post(app.config['SCRUM_API'] + '/update/sprintpeoplerecord', data=json.dumps(payload))


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

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/sprint_number/{1}'.format(project_id, str(int(sprint_data['sprint_number']) - 1)))
    previous_sprint_data = response.json()

    points_per_day = sprint_data['agreed_points'] / sprint_data['sprint_days']

    sprint_end_date = datetime.strptime(sprint_data['end_date'] + ' 23:59', '%Y-%m-%d %H:%M')
    current_sprint = False
    if (datetime.now() < sprint_end_date):
        current_sprint = True



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


    response = requests.get(app.config['SCRUM_API'] + '/get/daytypes/{0}'.format(project_id))
    daytype_data = response.json()

    weekend = set([5, 6])

    sprint_days = []
    day = 0
    for i in range(1, (int(sprint_data['sprint_days'])) +1):
        day = day + 1
        date = datetime.strptime(sprint_data['start_date'], '%Y-%m-%d') + timedelta(days=day)
        if date.weekday() in weekend:
            day += 1
            date = datetime.strptime(sprint_data['start_date'], '%Y-%m-%d') + timedelta(days=day)
            if date.weekday() in weekend:
                day += 1
                date = datetime.strptime(sprint_data['start_date'], '%Y-%m-%d') + timedelta(days=day)

        #print(day)

        sprint_days.append(date.strftime("%a"))



    return render_template('sprint.html', sprint_data=sprint_data, project_data=project_data, sprint_days_burndown=','.join(sprint_days_burndown), sprint_days_array=','.join(sprint_days_array), sprint_days_burndown_expected=','.join(sprint_days_burndown_expected), current_sprint=current_sprint, previous_sprint_data=previous_sprint_data, sprint_days=sprint_days, daytype_data=daytype_data)


@app.route('/project/<project_id>/<sprint_id>/burndown', methods=['GET', 'POST'])
def view_burndown(project_id, sprint_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()


    sprint_end_date = datetime.strptime(sprint_data['end_date'] + ' 23:59', '%Y-%m-%d %H:%M')
    current_sprint = False
    if (datetime.now() < sprint_end_date):
        current_sprint = True

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

    return render_template('burndown.html', sprint_data=sprint_data, project_data=project_data, sprint_days_burndown=','.join(sprint_days_burndown), sprint_days_array=','.join(sprint_days_array), sprint_days_burndown_expected=','.join(sprint_days_burndown_expected), current_sprint=current_sprint)


@app.route('/project/<project_id>/<sprint_id>/team', methods=['GET', 'POST'])
def view_team(project_id, sprint_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/daytypes/{0}'.format(project_id))
    daytype_data = response.json()

    weekend = set([5, 6])

    sprint_days = []
    day = 0
    for i in range(1, (int(sprint_data['sprint_days'])) +1):
        day = day + 1
        date = datetime.strptime(sprint_data['start_date'], '%Y-%m-%d') + timedelta(days=day)
        if date.weekday() in weekend:
            day += 1
            date = datetime.strptime(sprint_data['start_date'], '%Y-%m-%d') + timedelta(days=day)
            if date.weekday() in weekend:
                day += 1
                date = datetime.strptime(sprint_data['start_date'], '%Y-%m-%d') + timedelta(days=day)

        #print(day)

        sprint_days.append(date.strftime("%a"))

    return render_template('team.html', sprint_data=sprint_data, project_data=project_data, sprint_days=sprint_days, daytype_data=daytype_data)


@app.route('/project/<project_id>/<sprint_id>/team/update_team_availability', methods=['POST'])
@login_required
def update_team_availability(project_id, sprint_id):

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    payload = {"project_id":sprint_data['project_id'], "sprint_days": sprint_data['sprint_days'], "start_date": sprint_data['start_date'], "end_date": sprint_data['end_date'], "sprint_number": sprint_data['sprint_number'], "sprint_rag": sprint_data['sprint_rag'], "sprint_goal": sprint_data['sprint_goal'], "sprint_deliverables": sprint_data['sprint_deliverables'], "sprint_challenges": sprint_data['sprint_challenges'], "agreed_points": sprint_data['agreed_points'], "delivered_points": sprint_data['delivered_points'], "started_points": sprint_data['started_points'], "sprint_issues": sprint_data['sprint_issues'], "sprint_risks": sprint_data['sprint_risks'], "sprint_dependencies": sprint_data['sprint_dependencies'], "sprint_teamdays": request.form['amount_of_days']   }
    requests.post(app.config['SCRUM_API'] + '/update/sprint/{0}'.format(sprint_id), data=json.dumps(payload))

    return 'ok'




@app.route('/project/<project_id>/<sprint_id>/team/add_person', methods=['POST'])
@login_required
def add_person(project_id, sprint_id):

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    payload = {"sprint_id":sprint_id, "person_name": request.form['person_name'] }
    response = requests.post(app.config['SCRUM_API'] + '/add/sprintperson', data=json.dumps(payload))
    sprintperson_data = response.json()

    sprintperson_days_array = []
    for i in range(1, (int(sprint_data['sprint_days']) + 1)):
        sprintperson_days_array.append({"sprint_day": str(i), "sprint_daystatus": "0"})

    payload = {"sprintpeople_id": str(sprintperson_data['id']), "sprint_days": sprintperson_days_array}
    requests.post(app.config['SCRUM_API'] + '/update/sprintpeoplerecord', data=json.dumps(payload))

    return 'ok'


@app.route('/project/<project_id>/<sprint_id>/team/update_status/<sprintpeoplerecord_id>', methods=['POST'])
@login_required
def team_update_status(project_id, sprint_id, sprintpeoplerecord_id):

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    payload = {"sprint_daystatus": request.form['sprint_daystatus'] }
    response = requests.post(app.config['SCRUM_API'] + '/update/sprintpeoplerecord/{0}'.format(sprintpeoplerecord_id), data=json.dumps(payload))
    sprintperson_data = response.json()

    return 'ok'


@app.route('/project/<project_id>/<sprint_id>/json', methods=['GET'])
def script_json(project_id, sprint_id):

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))

    return response.text


@app.route('/project/<project_id>/<sprint_id>/team/remove_person', methods=['POST'])
@login_required
def delete_person(project_id, sprint_id):

    response = requests.get(app.config['SCRUM_API'] + '/delete/sprintperson/{0}'.format(request.form['person_id']))

    return 'ok'


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
                payload = {"project_id":project_id, "sprint_days": form.sprint_days.data, "start_date": str(form.start_date.data), "end_date": str(form.end_date.data), "sprint_number": form.sprint_number.data, "sprint_rag": form.sprint_rag.data, "sprint_goal": form.sprint_goal.data, "sprint_deliverables": form.sprint_deliverables.data, "sprint_challenges": form.sprint_challenges.data, "agreed_points": form.agreed_points.data, "delivered_points": sprint_data['delivered_points'], "started_points": form.started_points.data, "sprint_issues": form.sprint_issues.data, "sprint_risks": form.sprint_risks.data, "sprint_dependencies": form.sprint_dependencies.data, "sprint_teamdays": sprint_data['sprint_teamdays']  }
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
        form.delivery_manager.data  = project_data['delivery_manager']
        form.scrum_tool_link.data  = project_data['scrum_tool_link']

        return render_template('edit_project.html', project_data=project_data, form=form)
    else:
        if form.validate_on_submit():

            project_name_found = False;

            for d in programme_data['projects']:
                if d['name'] == form.project_name.data:
                    if str(d['id']) != project_id:
                        project_name_found = True

            if project_name_found == False:
                payload = {"project_name":form.project_name.data, "programme_id": project_data['programme_id'], "product_owner": form.product_owner.data, "scrum_master": form.scrum_master.data, "project_description": form.project_description.data, "delivery_manager": form.delivery_manager.data, "scrum_tool_link": form.scrum_tool_link.data}
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

        payload = {"project_id":sprint_data['project_id'], "sprint_days": sprint_data['sprint_days'], "start_date": sprint_data['start_date'], "end_date": sprint_data['end_date'], "sprint_number": sprint_data['sprint_number'], "sprint_rag": sprint_data['sprint_rag'], "sprint_goal": sprint_data['sprint_goal'], "sprint_deliverables": sprint_data['sprint_deliverables'], "sprint_challenges": sprint_data['sprint_challenges'], "agreed_points": sprint_data['agreed_points'], "delivered_points": str(points_done), "started_points": sprint_data['started_points'], "sprint_issues": sprint_data['sprint_issues'], "sprint_risks": sprint_data['sprint_risks'], "sprint_dependencies": sprint_data['sprint_dependencies'], "sprint_teamdays": sprint_data['sprint_teamdays']   }
        requests.post(app.config['SCRUM_API'] + '/update/sprint/{0}'.format(sprint_id), data=json.dumps(payload))

        flash('Burndown Updated')
        return redirect(url_for('sprint', project_id=project_id, sprint_id=sprint_id))


@app.route('/project/<project_id>/edit_sprint/<sprint_id>/daytypes', methods=['GET', 'POST'])
@login_required
def edit_daytypes(project_id, sprint_id):
    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}'.format(project_id, sprint_id))
    project_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/project/{0}/{1}'.format(project_id, sprint_id))
    sprint_data = response.json()

    response = requests.get(app.config['SCRUM_API'] + '/get/daytypes/{0}'.format(project_id))
    daytype_data = response.json()

    if request.method == 'GET':
        return render_template('edit_daytypes.html', project_data=project_data, sprint_data=sprint_data, daytype_data=daytype_data)
    else:
        daytype_id = request.form.getlist('daytype_id')
        daytype_name = request.form.getlist('daytype_name')
        daytype_status = request.form.getlist('daytype_status')
        daytype_day = request.form.getlist('daytype_day')
        daytype_color = request.form.getlist('daytype_color')
        daytype_order = request.form.getlist('daytype_order')

        print(daytype_id);

        for i in range(0, len(daytype_id)):
            if (daytype_id[i] == '0'):
                # add new
                payload = {"project_id": str(project_id), "daytype_status": daytype_status[i], 'daytype_name': daytype_name[i], 'daytype_day': daytype_day[i], 'daytype_color': daytype_color[i], 'daytype_order': daytype_order[i] }
                requests.post(app.config['SCRUM_API'] + '/add/daytype', data=json.dumps(payload))
            else:
                payload = {"daytype_status": daytype_status[i], 'daytype_name': daytype_name[i], 'daytype_day': daytype_day[i], 'daytype_color': daytype_color[i], 'daytype_order': daytype_order[i] }
                requests.post(app.config['SCRUM_API'] + '/update/daytype/{0}'.format(daytype_id[i]), data=json.dumps(payload))

        flash('Day Type Updated')
        return redirect(url_for('view_team', project_id=project_id, sprint_id=sprint_id))


@app.route('/project/<project_id>/edit_sprint/<sprint_id>/removedaytype/<daytype_id>', methods=['GET', 'POST'])
@login_required
def delete_daytype(project_id, sprint_id, daytype_id):
    response = requests.get(app.config['SCRUM_API'] + '/delete/daytype/{0}'.format(daytype_id))
    flash('Day Type Removed')
    return redirect(url_for('view_team', project_id=project_id, sprint_id=sprint_id))


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
