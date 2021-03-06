#!/usr/bin/env python

from fabric.api import run, sudo
from fabric.decorators import with_settings
from fabric.context_managers import shell_env  # , settings
from fabric.operations import put
from fabric.colors import red, green, yellow

USERNAME = 'takamaru'
FULLUSERNAME = 'Shoei Takamaru'


@with_settings(warn_only=True)
def update_apt_pkgs():
    if sudo('dpkg -s nginx | grep "install ok installed" > /dev/null').failed:
        sudo('apt-get update')
        sudo('apt-get upgrade -y')
        sudo('apt-get dist-upgrade -y')
        sudo('apt-get autoclean')
        sudo('apt-get autoremove -y')


@with_settings(warn_only=True)
def install_apt_pkgs():
    pkgs = [
        'apg',
        'build-essential',
        'colordiff',
        'ctags',
        'curl',
        'git',
        'imagemagick',
        'libbz2-dev',
        'libgd-dev',
        'libmysqlclient-dev',
        'libpq-dev',
        'libreadline-dev',
        'libreadline6-dev',
        'libsox-fmt-mp3',
        'libsqlite3-dev',
        'libssl-dev',
        'libxml2-dev',
        'libxslt-dev',
        'mailutils',
        'ncurses-term',      # xterm-256color
        'nkf',
        'ntp',
        'openssl',
        'postfix',
        'postgresql',
        'silversearcher-ag',
        'sox',
        'sqlite3',
        'sysstat',           # sar
        'sysv-rc-conf',
        'tk-dev',
        'traceroute',
        'vsftpd',
        'yasm',
        'zip',
        'zlib1g-dev',
    ]
    sudo('apt-get install -y ' + ' '.join(pkgs))


def install_nginx():
    sudo('apt-get install -y nginx')


def install_redis():
    sudo('apt-get install -y redis-server')


def install_mysql():
    # Skip interactive mode
    sudo('echo mysql-server mysql-server/root_password       password test | sudo debconf-set-selections')
    sudo('echo mysql-server mysql-server/root_password_again password test | sudo debconf-set-selections')

    sudo('apt-get install -y mysql-server')

@with_settings(warn_only=True)
def install_mosh():
    if sudo('dpkg -s mosh | grep "install ok installed" > /dev/null').failed:
        sudo('apt-get install -y python-software-properties')
        sudo('add-apt-repository -y ppa:keithw/mosh')
        sudo('apt-get update')
        sudo('apt-get install -y mosh')

@with_settings(warn_only=True)
def install_ffmpeg():
    if sudo('dpkg -s ffmpeg | grep "install ok installed" > /dev/null').failed:
        sudo('add-apt-repository -y ppa:mc3man/trusty-media')
        sudo('apt-get update')
        sudo('apt-get install -y ffmpeg')

@with_settings(warn_only=True, sudo_user=USERNAME)
def install_ruby():
    with shell_env(HOME='/home/' + USERNAME, PATH="/home/" + USERNAME + "/.rbenv/bin:$PATH"):
        # Install rbenv
        if sudo('test -d ~/.rbenv').failed:
            sudo('git clone https://github.com/sstephenson/rbenv.git ~/.rbenv')
            print green('"rbenv" installed')
        else:
            print green('"rbenv" is already installed')

        if sudo('grep ".rbenv" ~/.bashrc > /dev/null').failed:
            path_str = 'PATH="$HOME\/.rbenv\/bin:$PATH"'
            sudo('echo -e "\n# rbenv" >> ~/.bashrc')
            sudo('echo "export %s" >> ~/.bashrc')
            sudo("sed -i -e 's/%s/" + path_str + "/g' ~/.bashrc")
            print green('"rbenv PATH" configured')
        else:
            print green('"rbenv PATH" is already written')

        if sudo('grep "rbenv init" ~/.bashrc > /dev/null').failed:
            rb_str = '"$(rbenv init -)"'
            sudo('echo "eval %s" >> ~/.bashrc')
            sudo("sed -i -e 's/%s/" + rb_str + "/g' ~/.bashrc")
        else:
            print green('"rbenv" init is already written')

        # Install ruby-build
        if sudo('test -d ~/.rbenv/plugins/ruby-build').failed:
            sudo('git clone https://github.com/sstephenson/ruby-build.git ~/.rbenv/plugins/ruby-build')
        else:
            print green('"ruby-build" is already installed')

        # Install Ruby
        ruby_ver = sudo("rbenv install -l | awk '{print $1}' | egrep -v 'preview|dev|rc' | egrep --color=never '^2.1.[0-9](.*)$' | tail -1")    # 2.1.x
        if sudo('rbenv versions | grep --color=never "' + ruby_ver + '" > /dev/null').failed:
            sudo('rbenv install ' + ruby_ver)
        else:
            print green('"ruby %s" is already installed' % ruby_ver)
        sudo('rbenv global ' + ruby_ver)
        sudo('rbenv rehash')


@with_settings(warn_only=True, sudo_user=USERNAME)
def install_gems():
    with shell_env(HOME='/home/' + USERNAME, PATH="/home/" + USERNAME + "/.rbenv/bin:$PATH"):
        if sudo('test -f ~/.gemrc && grep "gem:" ~/.gemrc > /dev/null').failed:
            sudo('echo "gem: --no-ri --no-rdoc -V" >> ~/.gemrc')
        else:
            print green('".gemrc" already exists')

        gems = [
            'bundler',
            'pry',
            'rails',
            'rbenv-rehash',
            'rspec',
            'spring',
        ]

        not_installed = []
        installed = []
        for g in gems:
            if sudo("eval \"$(rbenv init -)\" && gem list | awk '{print $1}' | egrep '^" + g + "$' > /dev/null").failed:
                not_installed.append(g)
            else:
                installed.append(g)
        if len(installed) > 0:
            print green('"%s" is already installed') % ', '.join(installed)
        if len(not_installed) > 0:
            print yellow('"%s" is not installed') % ', '.join(not_installed)
            sudo('eval "$(rbenv init -)" && gem install ' + ' '.join(not_installed))

        sudo('rbenv rehash')


@with_settings(warn_only=True)
def create_user():
    if sudo('grep "' + USERNAME + '" /etc/sudoers > /dev/null').failed:
        sudo("sed -i -e '/^root/a " + USERNAME + " ALL=(ALL:ALL) ALL' /etc/sudoers")
    else:
        print green('"' + USERNAME + '" is already in sudoers')

    if run('cat /etc/passwd | grep ' + USERNAME + ' > /dev/null').succeeded:
        print green('"' + USERNAME + '" already exists')
        return

    params = {
        '-c': '"' + FULLUSERNAME + '"',
        '-d': '/home/' + USERNAME,
        '-s': '/bin/bash',
        '-m': USERNAME,    # -m and create USERNAME user
    }
    param_array = []
    for k, v in params.items():
        param_array.append(k + ' ' + v)

    sudo('useradd ' + ' '.join(param_array))


@with_settings(warn_only=True, sudo_user=USERNAME)
def put_rc_files():
    vimrc = '.vimrc'
    if run('test -f /home/' + USERNAME + '/' + vimrc).failed:
        put('~/' + vimrc, '~/' + vimrc)

        with shell_env(HOME='/home/' + USERNAME):
            sudo('cp ~vagrant/.vimrc ~')
            run('rm -f ~vagrant/.vimrc')
    else:
        print green('"%s" already exists' % vimrc)
        run('rm -f ~vagrant/.vimrc')

    gitconfig = '.gitconfig'
    if run('test -f /home/' + USERNAME + '/' + gitconfig).failed:
        put('~/' + gitconfig, '~/' + gitconfig)

        with shell_env(HOME='/home/' + USERNAME):
            sudo('cp ~vagrant/.gitconfig ~')
            run('rm -f ~vagrant/.gitconfig')
    else:
        print green('"%s" already exists' % gitconfig)
        run('rm -f ~vagrant/.gitconfig')

    inputrc = '.inputrc'
    if run('test -f /home/' + USERNAME + '/' + inputrc).failed:
        put('~/' + inputrc, '~/' + inputrc)

        with shell_env(HOME='/home/' + USERNAME):
            sudo('cp ~vagrant/.inputrc ~')
            run('rm -f ~vagrant/.inputrc')
    else:
        print green('"%s" already exists' % inputrc)
        run('rm -f ~vagrant/.inputrc')


@with_settings(warn_only=True, sudo_user=USERNAME)
def install_neobundle():
    with shell_env(HOME='/home/' + USERNAME):
        if sudo('test -d ~/.vim/bundle').failed:
            sudo('mkdir -p ~/.vim/bundle')
        else:
            print green('"~/.vim/bundle" already exists')

        if sudo('test -d ~/.vim/bundle/neobundle.vim').failed:
            sudo('git clone git://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim')
            sudo('~/.vim/bundle/neobundle.vim/bin/neoinstall')
        else:
            print green('"neobundle.vim" is already installed')


@with_settings(warn_only=True, sudo_user=USERNAME)
def modify_bashrc():
    with shell_env(HOME='/home/' + USERNAME):

        if run('grep "GIT_EDITOR=vim" ~/.bashrc > /dev/null').succeeded:
            print green('".bashrc" no need to modify')
            return

        sudo('echo -e "\n# aliases" >> ~/.bashrc')
        sudo("echo \"alias ls='ls -F --color'\" >> ~/.bashrc")
        sudo("echo \"alias grep='grep --color'\" >> ~/.bashrc")
        sudo("echo \"alias egrep='egrep --color'\" >> ~/.bashrc")
        sudo("echo \"alias less='less -R'\" >> ~/.bashrc")
        sudo('echo -e "\n# git" >> ~/.bashrc')
        sudo("echo 'export GIT_EDITOR=vim' >> ~/.bashrc")
        sudo("echo 'PS1=%s' >> ~/.bashrc")
        sudo("sed -i -e \"s/PS1=%s/PS1='%s'/\" ~/.bashrc")
        sudo("sed -i -e 's/%s/\[" + r'\\\\' + "u:" + r'\\\\' + "W$(__git_ps1 \"(%s)\")]$ /' ~/.bashrc")


@with_settings(warn_only=True, sudo_user=USERNAME)
def put_ssh_pubkey():
    macbook = 'takamario@Shoeis-MacBook-Air.local'

    put('~/.ssh/id_rsa.pub', '~/authorized_keys')

    if sudo('test -d ~' + USERNAME + '/.ssh').failed:
        sudo('mkdir -m 700 ~' + USERNAME + '/.ssh')
    else:
        print green('"~' + USERNAME + '/.ssh" already exists')

    if sudo('grep "' + macbook + '" ~' + USERNAME + '/.ssh/authorized_keys > /dev/null').failed:
        sudo('cat ~vagrant/authorized_keys >> ~' + USERNAME + '/.ssh/authorized_keys')
    else:
        print green('"ssh_pubkey" is already added')


@with_settings(warn_only=True, sudo_user=USERNAME)
def create_ssh_keys():
    if sudo('test -f ~' + USERNAME + '/.ssh/id_rsa').succeeded:
        print green('"ssh_seckey" already exists')
    else:
        if sudo('test -d ~' + USERNAME + '/.ssh').failed:
            sudo('mkdir -m 700 ~' + USERNAME + '/.ssh')
        else:
            print green('"~' + USERNAME + '/.ssh" already exists')
        sudo('ssh-keygen -t rsa -N "" -f ~' + USERNAME + '/.ssh/id_rsa')


@with_settings(warn_only=True, sudo_user=USERNAME)
def install_nodejs():
    with shell_env(HOME='/home/' + USERNAME):
        if sudo('test -d ~/.nvm').succeeded:
            print green('"nvm" is already installed')
        else:
            # Install nvm
            sudo('curl -s https://raw.github.com/creationix/nvm/master/install.sh | sh')
            sudo("echo 'export NVM_HOME=\"$HOME/.nvm\"' >> ~/.profile")

        # Install node
        if sudo('. $HOME/.nvm/nvm.sh && which node').failed:
            current_stable = sudo("curl -s http://nodejs.org | grep -i 'current version' | sed -e 's/\(.*\)current version: \(v[0-9]*\.[0-9]*\.[0-9]*\)\(.*\)/" + '\\' + "2/i'")
            sudo('. $HOME/.nvm/nvm.sh && nvm install ' + current_stable)
            sudo('. $HOME/.nvm/nvm.sh && nvm use ' + current_stable)
            sudo('. $HOME/.nvm/nvm.sh && nvm alias default ' + current_stable)
        else:
            print green('"node.js" is already installed')


@with_settings(warn_only=True, sudo_user=USERNAME)
def install_npms():
    with shell_env(HOME='/home/' + USERNAME):
        npms = [
            'bower',
            'coffee-script',
            'coffeelint',
            'express-generator',
            'grunt-cli',
            'jasmine-node',
            'js-fixtures',
            'js2coffee',
            'jshint',
            'karma',
            'karma-coverage',
            'karma-expect',
            'karma-mocha',
            'karma-chai',
            'mocha',
            'ngmin',
            'node-dev',
            'phantomjs',
            'uglify-js',
            'yo',
        ]

        not_installed = []
        installed = []
        for n in npms:
            if sudo(". $HOME/.nvm/nvm.sh && npm list -g --parseable | egrep 'lib/node_modules/" + n + "$' > /dev/null").failed:
                not_installed.append(n)
            else:
                installed.append(n)
        if len(installed) > 0:
            print green('"%s" is already installed') % ', '.join(installed)
        if len(not_installed) > 0:
            print yellow('"%s" is not installed') % ', '.join(not_installed)
            sudo('. $HOME/.nvm/nvm.sh && npm install -g ' + ' '.join(not_installed))


@with_settings(warn_only=True, sudo_user=USERNAME)
def install_python():
    with shell_env(HOME='/home/' + USERNAME, PATH="/home/" + USERNAME + "/.pyenv/bin:$PATH"):
        # Install pyenv
        if sudo('test -d ~/.pyenv').failed:
            sudo('git clone https://github.com/yyuu/pyenv.git ~/.pyenv')
        else:
            print green('"pyenv" is already installed')

        if sudo('grep ".pyenv" ~/.bashrc > /dev/null').failed:
            pyenv_root = 'PYENV_ROOT="$HOME\/.pyenv"'
            path_str = 'PATH="$PYENV_ROOT\/bin:$PATH"'
            sudo('echo -e "\n# pyenv" >> ~/.bashrc')
            sudo('echo "export %s" >> ~/.bashrc')
            sudo("sed -i -e 's/%s/" + pyenv_root + "/g' ~/.bashrc")
            sudo('echo "export %s" >> ~/.bashrc')
            sudo("sed -i -e 's/%s/" + path_str + "/g' ~/.bashrc")
        else:
            print green('"pyenv PATH" is already written')

        if sudo('grep "pyenv init" ~/.bashrc > /dev/null').failed:
            py_str = '"$(pyenv init -)"'
            sudo('echo "eval %s" >> ~/.bashrc')
            sudo("sed -i -e 's/%s/" + py_str + "/g' ~/.bashrc")
        else:
            print green('"pyenv" init is already written')

        # Install Python
        python_ver = sudo("pyenv install -l | awk '{print $1}' | egrep --color=never '^2\.7\.[0-9.]+' | tail -1")    # 2.7.x
        if sudo('pyenv versions | grep --color=never "' + python_ver + '" > /dev/null').failed:
            sudo('pyenv install ' + python_ver)
        else:
            print green('"python %s" is already installed' % python_ver)
        sudo('pyenv global ' + python_ver)
        sudo('pyenv rehash')


@with_settings(warn_only=True, sudo_user=USERNAME)
def install_pip():
    with shell_env(HOME='/home/' + USERNAME, PATH="/home/" + USERNAME + "/.pyenv/bin:$PATH"):
        pips = [
            'flake8',
        ]

        not_installed = []
        installed = []
        for p in pips:
            if sudo("eval \"$(pyenv init -)\" && pip list | awk '{print $1}' | egrep --color=never '^" + p + "$' > /dev/null").failed:
                not_installed.append(p)
            else:
                installed.append(p)
        if len(installed) > 0:
            print green('"%s" is already installed') % ', '.join(installed)
        if len(not_installed) > 0:
            print yellow('"%s" is not installed') % ', '.join(not_installed)
            sudo('eval "$(pyenv init -)" && pip install ' + ' '.join(not_installed))


@with_settings(warn_only=True)
def install_ja_locale():
    if sudo('locale -a | grep "ja_JP"').failed:
        sudo('locale-gen ja_JP.UTF-8')
    else:
        print green('"ja_JP.UTF-8" is already installed')


@with_settings(warn_only=True)
def configure_ntp():
    if sudo('grep "mfeed.ad.jp" /etc/ntp.conf > /dev/null').failed:
        sudo("sed -i -e 's/^\(server *\)/#" + r'\\' +"1/' /etc/ntp.conf")
        sudo("sed -i -e '/^#server ntp.ubuntu.com/a server ntp.jst.mfeed.ad.jp iburst" + r'\\' + "nserver ntp.ring.gr.jp iburst' /etc/ntp.conf")
    else:
        print green('"ntp" is already configured')


@with_settings(warn_only=True)
def set_utc():
    tz_str = 'Etc/UTC'
    if sudo('grep "' + tz_str + '" /etc/timezone > /dev/null').failed:
        sudo("echo '" + tz_str + "' > /etc/timezone")
        sudo('dpkg-reconfigure -f noninteractive tzdata')
    else:
        print green('"UTC" is already used')


@with_settings(warn_only=True)
def install_heroku_toolbelt():
    if run('which heroku > /dev/null').failed:
        print yellow('"heroku toolbelt" is not installed')
        run('wget -qO- https://toolbelt.heroku.com/install-ubuntu.sh | sh')
    else:
        print green('"heroku toolbelt" is already installed')


@with_settings(warn_only=True)
def install_go():
    if run('which go > /dev/null').failed:
        if run('test -d /usr/local/go').failed:
            version = 'go1.2.linux-amd64.tar.gz'
            print yellow('"Go" is not installed')
            run('wget -O /tmp/' + version + ' https://go.googlecode.com/files/' + version)
            sudo('tar -C /usr/local -xf /tmp/' + version)
            run('rm /tmp/' + version)
        if run('grep "/usr/local/go/bin" /home/' + USERNAME + '/.bashrc > /dev/null').failed:
            sudo("echo 'export PATH=\"/usr/local/go/bin:$PATH\"' >> /home/" + USERNAME + '/.bashrc')
        print green('"Go" is successfully installed')
    else:
        print green('"Go" is already installed')


def install_middlewares():
    update_apt_pkgs()
    install_apt_pkgs()
    install_nginx()
    install_redis()
    #install_mysql()
    install_mosh()
    install_ffmpeg()
    create_user()
    install_ruby()
    install_gems()
    install_nodejs()
    install_npms()
    install_python()
    install_pip()
    put_rc_files()
    modify_bashrc()
    install_neobundle()
    put_ssh_pubkey()
    create_ssh_keys()
    install_ja_locale()
    configure_ntp()
    set_utc()
    install_heroku_toolbelt()
    install_go()
