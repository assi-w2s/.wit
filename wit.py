import os
import shutil
import random
import datetime
import filecmp


def get_parts(path):
    '''returns the parts of a path'''
    current_path = ''
    for char in path:
        if char in r"\/":
            yield current_path
            current_path = ""
        else:
            current_path += char
    if current_path is not "":
        yield current_path


def find_paths(BU_relative_path=''):
    path_parts = list(get_parts(os.getcwd()))
    while ':' not in path_parts[-1]:
        if os.path.isdir('.wit'):
            basedir_path = '\\'.join(path_parts)
            break
        else:
            os.chdir('..')
            BU_relative_path = path_parts.pop() + '\\' + BU_relative_path

    if ':' in path_parts[-1]:
        raise FileNotFoundError("No valid .wit directory was found.")

    return basedir_path, BU_relative_path


def init():
    '''wit init: initiates .wit folder containing (i) images, (ii) staging_area and activated.txt file'''
    init_dir = os.path.join(os.getcwd(), '.wit')
    if os.path.exists(init_dir):
        raise OSError("'.wit' Directory already exists.")
        # check to add sys.exit("...")
    else:
        os.mkdir(init_dir)

        image_dir = init_dir + '\images'
        os.mkdir(image_dir)

        staging_dir = init_dir + '\staging_area'
        os.mkdir(staging_dir)
        print(f"wit project initiated in {init_dir}")

        with open(os.path.join(init_dir, 'activated.txt'), 'w') as act_f:
            act_f.write("master")


def add(BU_partial_path):
    '''wit add'''
    basedir_path, BU_relative_path = find_paths(BU_partial_path)
    staging_path = os.path.join(basedir_path, '.wit\\staging_area')

    backup_src_dir = os.path.join(basedir_path, BU_relative_path)
    staging_dst_dir = os.path.join(staging_path, BU_relative_path)

    if os.path.isfile(backup_src_dir):
        if os.path.exists(staging_dst_dir):
            if filecmp.cmp(backup_src_dir, staging_dst_dir):
                return
            else:
                os.remove(staging_dst_dir)
        elif not os.path.exists(staging_dst_dir.rsplit('\\', 1)[0]):
            os.mkdir(staging_dst_dir.rsplit('\\', 1)[0])
        shutil.copy(backup_src_dir, staging_dst_dir)


    else:
        for src_dir, dirs, files in os.walk(backup_src_dir):
            dst_dir = src_dir.replace(backup_src_dir, staging_dst_dir, 1)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    if os.path.samefile(src_file, dst_file):
                        continue
                    else:
                        os.remove(dst_file)
                shutil.copy(src_file, dst_dir)

    print(f"{BU_relative_path!r} added to staging area.")


def return_h_m(basedir_path):
    '''returns the head and master paths'''
    try:
        with open(os.path.join(basedir_path, '.wit', 'references.txt'), 'r') as ref_f:
            ref_c = ref_f.readlines()
        head = ref_c[0].split('=')[1].rstrip('\n')
        master = ref_c[1].split('=')[1].rstrip('\n')
        return head, master
    except FileNotFoundError or IndexError:
        head = 'None'
        return head, head


def commit(message):
    '''wit commit'''
    commit_id = ''.join(random.choice('1234567890abcdef') for _ in range(40))
    base_dir, _ = find_paths()
    old_head, master = return_h_m(base_dir)
    staging_dir = os.path.join(base_dir, '.wit', 'staging_area')
    new_head_dir = os.path.join(base_dir, '.wit', 'images', commit_id)
    '''
    before updating head:
        check branch in ref file
        if branch   
    '''

    with open(new_head_dir + '.txt', 'w') as f:
        f.write(
            f'parent={old_head}\n'+
            f'date={datetime.datetime.now().strftime("%c +0300")}\n'
            f'message={message}'
        )

    shutil.copytree(staging_dir, new_head_dir)
    ref_fp = os.path.join(base_dir, '.wit', 'references.txt')

    activated_fp = os.path.join(base_dir, '.wit', 'activated.txt')
    with open(activated_fp, 'r') as act_f:
        activated = act_f.read()

    try:
        with open(ref_fp, 'r') as ref_f:
            ref_fc = [line.strip() for line in ref_f.readlines()]

        name_id_list = [line.split('=') for line in ref_fc]
        for idx, name_id in enumerate(name_id_list):
            if name_id[0] == 'HEAD':
                name_id_list[idx][1] = commit_id
            elif name_id[0] == 'master' and name_id[1] == old_head:
                name_id_list[idx][1] = commit_id
            elif name_id[0] == activated and name_id[1] == old_head:
                name_id_list[idx][1] = commit_id

        new_ref_fc = '\n'.join([name + '=' + id for name, id in name_id_list])

    except FileNotFoundError:
        new_ref_fc = (
            f'HEAD={commit_id}\n'
            f'master={commit_id}\n'
        )

    with open(ref_fp, 'w') as ref_f:
        ref_f.writelines(new_ref_fc)

    print(f"Commit {commit_id} created")


def status(checkout=False):
    '''wit status'''
    base_dir, _ = find_paths()
    stage_dir = os.path.join(base_dir, '.wit', 'staging_area')
    image_dir = os.path.join(base_dir, '.wit', 'images')
    head, _ = return_h_m(base_dir)
    wit_files = {'Changes to be committed:':[], 'Changes not staged for commit:':[], 'Untracked files:': []}

    for root_src_dir, dirs, files in os.walk(base_dir):
        if '.wit' in root_src_dir:
            continue
        for file in files:
            orig_file = os.path.join(root_src_dir, file)
            stage_file = os.path.join(stage_dir, root_src_dir.rsplit(base_dir, 1)[1].strip('\\'), file)
            commit_id_file = os.path.join(image_dir, head, root_src_dir.rsplit(base_dir, 1)[1].strip('\\'), file)

            if not os.path.exists(stage_file):
                wit_files['Untracked files:'].append(orig_file)
            elif filecmp.cmp(orig_file, stage_file) and not os.path.exists(commit_id_file):
                wit_files['Changes to be committed:'].append(stage_file)
            elif not filecmp.cmp(orig_file, stage_file):
                wit_files['Changes not staged for commit:'].append(orig_file)

    if not checkout:
        print(f"\nCommit ID: {head}")
        for file_type, file_names in wit_files.items():
            print('\n' + file_type)
            for file_name in file_names:
                print(file_name)
        return

    if wit_files.get('Changes not staged for commit:') or wit_files.get('Changes to be committed:'):
        return False
    else:
        return True


def checkout(commit_id):
    '''wit checkout'''
    base_dir, _ = find_paths()

    staging_dir = os.path.join(base_dir, '.wit', 'staging_area')
    ref_fp = os.path.join(base_dir, '.wit', 'references.txt')
    checkout_branch = False

    if len(commit_id) is not 40:  # meaning it's not a commit_id, but a branch name
        '''
        open referernces file
        search for branch name
        take branch's name as the commit's id
        continue
        '''
        checkout_branch = True
        name = commit_id
        with open(ref_fp, 'r') as ref_f:
            ref_fc = ref_f.readlines()

        for line in ref_fc:
            branch_name, branch_commit_id = line.split('=')
            if branch_name == name:
                commit_id = branch_commit_id.strip()
                break

    commit_id_dir = os.path.join(base_dir, '.wit', 'images', commit_id)
    if not status(checkout=True):
        print("Checkout can't be executed as there are changes to be committed / not staged for commit; Please check wit status")
        return
    else:
        for src_dir, dirs, files in os.walk(commit_id_dir):
            dst_dir = src_dir.replace(commit_id_dir, base_dir, 1)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.copy(src_file, dst_dir)

        shutil.rmtree(staging_dir)
        shutil.copytree(commit_id_dir, staging_dir)

    with open(ref_fp, 'r') as ref_f:
        ref_c = ref_f.readlines()
    ref_c[0] = f'HEAD={commit_id}\n'
    with open(ref_fp, 'w') as ref_f:
        ref_f.writelines(ref_c)

    if checkout_branch:
        activated_fp = os.path.join(base_dir, '.wit', 'activated.txt')
        with open(activated_fp, 'w') as act_f:
            act_f.write(branch_name)


def graph(show_all=None):
    '''wit graph - plots the current graph for the different branches'''
    base_dir, _ = find_paths()
    image_dir = os.path.join(base_dir, '.wit', 'images')
    images = {}
    head, master = return_h_m(base_dir)

    for file in os.listdir(image_dir):
        file_path = os.path.join(image_dir, file)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                parent = f.readlines()[0].strip().split('=')[1]
            images[file.strip('.txt')] = parent

    wit_chart = graphviz.Digraph(comment='.wit Chart')

    wit_chart.node("HEAD", "HEAD")
    wit_chart.node('...' + head[-5:],'...' + head[-5:])
    wit_chart.edge("HEAD",'...' + head[-5:])

    wit_chart.node("master", "master")
    wit_chart.node('...' +master[-5:],'...' + master[-5:])
    wit_chart.edge("master",'...' + master[-5:])

    if show_all:
        for head, parent in images.items():
            if parent == 'None':
                continue
            wit_chart.node('...' + head[-5:])
            wit_chart.node('...' + parent[-5:])
            wit_chart.edge('...' + head[-5:],'...' + parent[-5:])

    elif not show_all:
        parent = images[head]

        while images.get(parent):
            wit_chart.node('...' + parent[-5:],'...' + parent[-5:])
            wit_chart.edge('...' + head[-5:],'...' + parent[-5:])
            head = parent
            parent = images[head]

    wit_chart.render(view=True)


def branch(name):
    '''wit branch'''
    base_dir, _ = find_paths(os.getcwd())
    head, master = return_h_m(base_dir)
    references_fp = os.path.join(base_dir, '.wit', 'references.txt')

    with open(references_fp, 'r+') as ref_f:
        ref_fc = ref_f.readlines()
        for line in ref_fc:
            if name == line.split('=')[0]:
                print(f"This branch name ({name!r}) already exists;")
                return
        ref_f.write(f'\n{name}={head}')


if __name__ == "__main__":
    if sys.argv[1] == 'init':
        init()

    if sys.argv[1] == 'add':
        add(sys.argv[2])

    if sys.argv[1] == 'commit' and find_paths():
        commit(sys.argv[2])

    if sys.argv[1] == 'status' and find_paths():
        status()

    if sys.argv[1] == 'checkout' and find_paths():
        checkout(sys.argv[2])

    if sys.argv[1] == 'graph':
        args = [arg for arg in sys.argv[1:]]
        if "--all" in args:
            graph(show_all=True)
        else:
            graph()

    if sys.argv[1] == 'branch':
        branch(sys.argv[2])
