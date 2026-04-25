from pathlib import Path

from flask import Flask, render_template, redirect, abort, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from data import db_session
from data.users import User
from data.jobs import Jobs
from data.friendships import Friendship
from forms.user import RegisterForm, LoginForm
from forms.job import JobForm


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'db' / 'mars_explorer.sqlite'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Сначала войдите в систему'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, int(user_id))
    db_sess.close()
    return user


def is_admin(user: User) -> bool:
    return user.is_authenticated and user.id == 1


def can_manage_job(job: Jobs) -> bool:
    return current_user.is_authenticated and (
        job.team_leader == current_user.id or is_admin(current_user)
    )


def get_user_jobs(db_sess, user_id):
    return db_sess.query(Jobs).filter(Jobs.team_leader == user_id).all()


def is_friend(db_sess, user_id, friend_id):
    return db_sess.query(Friendship).filter(
        Friendship.user_id == user_id,
        Friendship.friend_id == friend_id
    ).first() is not None


@app.route('/')
@app.route('/index')
def main_page():
    db_sess = db_session.create_session()
    jobs = db_sess.query(Jobs).all()
    actions = [
        [
            job.id,
            job.job,
            job.work_size,
            job.collaborators,
            job.is_finished,
            job.user.name if job.user else '',
            job.user.surname if job.user else '',
            job.team_leader
        ]
        for job in jobs
    ]
    db_sess.close()
    return render_template('index.html', title='Главная', actions=actions)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        existing_user = db_sess.query(User).filter(User.email == form.email.data).first()
        if existing_user:
            db_sess.close()
            return render_template('register.html', title='Регистрация', form=form,
                                   message='Такой пользователь уже существует')

        user = User(
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            position=form.position.data,
            speciality=form.speciality.data,
            address=form.address.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        flash('Регистрация прошла успешно', 'success')
        return redirect('/login')

    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        db_sess.close()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Вы успешно вошли в систему', 'success')
            return redirect('/')

        return render_template('login.html', title='Авторизация',
                               message='Неправильный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'success')
    return redirect('/')


@app.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_job():
    form = JobForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        job = Jobs(
            team_leader=current_user.id,
            job=form.job.data,
            work_size=form.work_size.data,
            collaborators=form.collaborators.data,
            is_finished=form.is_finished.data,
        )
        db_sess.add(job)
        db_sess.commit()
        db_sess.close()
        flash('Работа успешно добавлена', 'success')
        return redirect('/')
    return render_template('job.html', title='Добавление работы', form=form)


@app.route('/personal')
@login_required
def personal_page():
    db_sess = db_session.create_session()
    my_jobs = get_user_jobs(db_sess, current_user.id)
    total_jobs = len(my_jobs)
    finished_jobs = len([job for job in my_jobs if job.is_finished])
    active_jobs = total_jobs - finished_jobs
    total_hours = sum(job.work_size or 0 for job in my_jobs)
    db_sess.close()
    return render_template('personal.html', title='Личный кабинет',
                           total_jobs=total_jobs, finished_jobs=finished_jobs,
                           active_jobs=active_jobs, total_hours=total_hours)


@app.route('/dashboard')
@login_required
def dashboard():
    db_sess = db_session.create_session()

    jobs = db_sess.query(Jobs).all()
    users = db_sess.query(User).all()
    friendships = db_sess.query(Friendship).all()

    total = len(jobs)
    done = len([job for job in jobs if job.is_finished])
    in_progress = total - done
    total_hours = sum(job.work_size or 0 for job in jobs)

    my_jobs = [job for job in jobs if job.team_leader == current_user.id]
    my_total = len(my_jobs)
    my_done = len([job for job in my_jobs if job.is_finished])
    my_in_progress = my_total - my_done

    total_users = len(users)
    total_friendships = len(friendships)

    db_sess.close()

    return render_template(
        'dashboard.html',
        title='Dashboard',
        total=total,
        done=done,
        in_progress=in_progress,
        total_hours=total_hours,
        my_total=my_total,
        my_done=my_done,
        my_in_progress=my_in_progress,
        total_users=total_users,
        total_friendships=total_friendships
    )


@app.route('/delete_job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    db_sess = db_session.create_session()
    job = db_sess.query(Jobs).filter(Jobs.id == job_id).first()
    if not job:
        db_sess.close()
        abort(404)

    if not can_manage_job(job):
        db_sess.close()
        abort(403)

    db_sess.delete(job)
    db_sess.commit()
    db_sess.close()
    flash('Работа успешно удалена', 'success')
    return redirect('/')


@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    form = JobForm()
    db_sess = db_session.create_session()
    job = db_sess.query(Jobs).filter(Jobs.id == job_id).first()

    if not job:
        db_sess.close()
        abort(404)

    if not can_manage_job(job):
        db_sess.close()
        abort(403)

    if request.method == 'GET':
        form.job.data = job.job
        form.work_size.data = job.work_size
        form.collaborators.data = job.collaborators
        form.is_finished.data = job.is_finished

    if form.validate_on_submit():
        job.job = form.job.data
        job.work_size = form.work_size.data
        job.collaborators = form.collaborators.data
        job.is_finished = form.is_finished.data
        db_sess.commit()
        db_sess.close()
        flash('Работа успешно изменена', 'success')
        return redirect('/')

    db_sess.close()
    return render_template('job.html', title='Редактирование работы', form=form)


@app.route('/users')
@login_required
def users_page():
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.id != current_user.id).all()
    friend_ids = [
        friendship.friend_id
        for friendship in db_sess.query(Friendship).filter(Friendship.user_id == current_user.id).all()
    ]
    db_sess.close()
    return render_template('users.html', title='Пользователи',
                           users=users, friend_ids=friend_ids)


@app.route('/friends')
@login_required
def friends_page():
    db_sess = db_session.create_session()
    friendships = db_sess.query(Friendship).filter(Friendship.user_id == current_user.id).all()
    friend_ids = [friendship.friend_id for friendship in friendships]
    friends = db_sess.query(User).filter(User.id.in_(friend_ids)).all() if friend_ids else []
    db_sess.close()
    return render_template('friends.html', title='Мои друзья', friends=friends)


@app.route('/add_friend/<int:user_id>', methods=['POST'])
@login_required
def add_friend(user_id):
    if user_id == current_user.id:
        flash('Нельзя добавить самого себя в друзья', 'warning')
        return redirect('/users')

    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        db_sess.close()
        abort(404)

    if is_friend(db_sess, current_user.id, user_id):
        db_sess.close()
        flash('Этот пользователь уже есть в друзьях', 'warning')
        return redirect('/users')

    friendship = Friendship(user_id=current_user.id, friend_id=user_id)
    db_sess.add(friendship)
    db_sess.commit()
    db_sess.close()
    flash('Пользователь добавлен в друзья', 'success')
    return redirect('/friends')


@app.route('/remove_friend/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    db_sess = db_session.create_session()
    friendship = db_sess.query(Friendship).filter(
        Friendship.user_id == current_user.id,
        Friendship.friend_id == user_id
    ).first()

    if not friendship:
        db_sess.close()
        abort(404)

    db_sess.delete(friendship)
    db_sess.commit()
    db_sess.close()
    flash('Пользователь удалён из друзей', 'success')
    return redirect('/friends')


@app.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        db_sess.close()
        abort(404)

    allowed = (
        user.id == current_user.id
        or is_admin(current_user)
        or is_friend(db_sess, current_user.id, user.id)
    )
    if not allowed:
        db_sess.close()
        abort(403)

    jobs = get_user_jobs(db_sess, user.id)
    db_sess.close()
    return render_template('user_profile.html', title='Профиль пользователя',
                           profile_user=user, jobs=jobs)


def main():
    db_session.global_init(str(DB_PATH))
    app.run(host='0.0.0.0', port=5001)


if __name__ == '__main__':
    main()
