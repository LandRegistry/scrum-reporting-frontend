from wtforms import BooleanField, TextField, PasswordField, validators, IntegerField, SelectField
from wtforms.widgets import TextArea
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, ValidationError, NumberRange, Email
from flask.ext.wtf import Form


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])

class ProgrammeForm(Form):
    programme_name = TextField('Programme Name', [validators.Length(min=1, max=200)])
    programme_manager = TextField('Programme Manager', [validators.Length(min=1, max=200)])
    service_manager = TextField('Service Manager', [validators.Length(min=1, max=200)])

class ProjectForm(Form):
    project_name = TextField('Project Name', [validators.Length(min=1, max=200)])
    product_owner = TextField('Product Owner', [validators.Length(min=1, max=200)])
    scrum_master = TextField('Scrum Master', [validators.Length(min=1, max=200)])
    delivery_manager = TextField('Delivery Manager', [validators.Length(min=1, max=299)])
    scrum_tool_link = TextField('Scrum Tool Link', [validators.Length(min=1, max=600)])
    project_description = TextField('Project Description', [validators.Length(min=1, max=2000)], widget=TextArea())

class SprintForm(Form):
    sprint_number = IntegerField('Sprint Number', [validators.required(), validators.NumberRange(min=1)])
    agreed_points = IntegerField('Planned Points')
    sprint_deliverables = TextField('Sprint Deliverables', [validators.Length(min=0, max=2000)], widget=TextArea())
    started_points = IntegerField('Points Started')
    delivered_points = IntegerField('Points Deliverabled')
    sprint_dependencies = TextField('Sprint Dependencies', [validators.Length(min=0, max=2000)], widget=TextArea())
    end_date = DateField('DatePicker', format='%Y-%m-%d')
    start_date = DateField('DatePicker', format='%Y-%m-%d')
    sprint_days = SelectField('Sprint Duration (Working Days)', choices=[('5', '5'), ('10', '10'), ('15', '15'), ('20', '20')], default='10')
    sprint_risks = TextField('Sprint Risks', [validators.Length(min=0, max=2000)], widget=TextArea())
    sprint_goal = TextField('Sprint Goal', [validators.Length(min=0, max=2000)], widget=TextArea())
    sprint_rag = SelectField('Sprint RAG', choices=[('r', 'Red'), ('a', 'Amber'), ('g', 'Green')], default='a')
    sprint_challenges = TextField('Sprint Challenges', [validators.Length(min=0, max=2000)], widget=TextArea())
    sprint_issues = TextField('Sprint Issues', [validators.Length(min=0, max=2000)], widget=TextArea())
    burndown_type = SelectField('Burndown Type', choices=[('0', 'Points'), ('1', 'Hours')], default='0')
    burndown_total = IntegerField('Burndown Hours Total')
