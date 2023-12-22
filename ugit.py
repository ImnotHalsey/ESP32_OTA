import os,hashlib
import urequests,time
import json,network
import machine,binascii

class GitHubUpdater:
    def __init__(self, user='ImnotHalsey', repository='ESP32_OTA',
                 token='', default_branch='main', ignore_files=None):
        self.user = user
        self.repository = repository
        self.token = token
        self.default_branch = default_branch
        self.ignore_files = ignore_files or ['/ugit.py', '/boot.py','/wifimanager.py','/wifi.dat']
        self.ignore = self.ignore_files
        self.internal_tree = []  # Define internal_tree as an instance variable

        # Static URLS
        self.giturl = f'https://github.com/{self.user}/{self.repository}'
        self.call_trees_url = f'https://api.github.com/repos/ImnotHalsey/ESP32_OTA/git/trees/main?recursive=1'
        self.raw = f'https://raw.githubusercontent.com/{self.user}/{self.repository}/master/'
        self.version_url = "https://raw.githubusercontent.com/ImnotHalsey/ESP32_OTA/main/version.json"

    
    def pull(self, f_path, raw_url):
        print(f'pulling {f_path} from github')
        print("Raw: ", raw_url)
        headers = {'User-Agent': 'ImnotHalsey-ESP32_OTA'}
        if len(self.token) > 0:
            headers['authorization'] = "bearer %s" % self.token
        r = urequests.get(raw_url, headers=headers)
        try:
            new_file = open(f_path, 'w')
            new_file.write(r.content.decode('utf-8'))
            new_file.close()
        except:
            print('decode fail try adding non-code files to .gitignore')
            try:
                new_file.close()
            except:
                print('tried to close new_file to save memory during raw file decode')

    def pull_all(self):
        os.chdir('/')
        tree = self.pull_git_tree()
        self.internal_tree = self.build_internal_tree()  # Use self.internal_tree
        self.internal_tree = self.remove_ignore(self.internal_tree)
        print(' Ignore removed ----------------------')
        print(self.internal_tree)
        log = []
        print("Done Till Log Creating .. 51")
        
        
        # Download and save all files
        for i in tree['tree']:
            if i['type'] == 'tree':
                try:
                    os.mkdir(i['path'])
                except:
                    print(f'Failed to create {i["path"]} directory; it may already exist.')
            elif i['path'] not in self.ignore:
                try:
                    os.remove(i['path'])
                    log.append(f'{i["path"]} file removed from internal memory')
                    self.internal_tree = self.remove_item(i['path'], self.internal_tree)
                except:
                    log.append(f'{i["path"]} deletion failed from internal memory')
                    print('Failed to delete the old file')
                try:
                    self.pull(i['path'], self.raw + i['path'])
                    log.append(f'{i["path"]} updated')
                except:
                    log.append(f'{i["path"]} failed to pull')
        # Delete files not in the GitHub tree
        if len(self.internal_tree) > 0:
            print(self.internal_tree, ' leftover!')
            for i in self.internal_tree:
                os.remove(i)
                log.append(f'{i} removed from internal memory')
        logfile = open('ugit_log.py', 'w')
        logfile.write(str(log))
        logfile.close()
        time.sleep(10)
        print('Resetting machine in 10 seconds: machine.reset()')
        machine.reset()
        
    def build_internal_tree(self):
        os.chdir('/')
        for i in os.listdir():
            self.add_to_tree(i)
        return self.internal_tree  # Use self.internal_tree
    
    def add_to_tree(self, dir_item):
        if self.is_directory(dir_item) and len(os.listdir(dir_item)) >= 1:
            os.chdir(dir_item)
            for i in os.listdir():
                self.add_to_tree(i)
            os.chdir('..')
        else:
            print(dir_item)
            if os.getcwd() != '/':
                subfile_path = os.getcwd() + '/' + dir_item
            else:
                subfile_path = os.getcwd() + dir_item
            try:
                print(f'sub_path: {subfile_path}')
                self.internal_tree.append([subfile_path, self.get_hash(subfile_path)])
            except OSError:  # type: ignore # for removing the type error indicator :)
                print(f'{dir_item} could not be added to tree')
                
    def get_hash(self, file):
        print(file)
        try:
            with open(file, 'r') as o_file:
                r_file = o_file.read()
                sha1obj = hashlib.sha1(r_file)
                hash = sha1obj.digest()
                return binascii.hexlify(hash)
        except OSError as e:
            print(f'Error reading {file}. Error: {e}')

    def remove_ignore(self, internal_tree):
        clean_tree = []
        int_tree = []
        for i in internal_tree:
            int_tree.append(i[0])
        for i in int_tree:
            if i not in self.ignore:
                clean_tree.append(i)
        return clean_tree
    
    def pull_git_tree(self):
        headers = {'User-Agent': 'ImnotHalsey-ESP32_OTA'}
        if len(self.token) > 0:
            headers['authorization'] = "bearer %s" % self.token
        try:
            r = urequests.get(self.call_trees_url, headers=headers)
            data = json.loads(r.content.decode('utf-8'))
            if 'tree' not in data:
                print(f'\nDefault branch "main" not found. Set "default_branch" variable to your default branch.\n')
                raise Exception(f'Default branch {self.default_branch} not found.')
            tree = json.loads(r.content.decode('utf-8'))
            return tree
        except Exception as e:
            print(f'Error: {e}')

            
    def is_directory(self, file):
        try:
            return os.stat(file)[8] == 0
        except:
            return False
        
    def remove_ignore(self, internal_tree):
        clean_tree = []
        int_tree = []
        for i in internal_tree:
            int_tree.append(i[0])
        for i in int_tree:
            if i not in self.ignore:
                clean_tree.append(i)
        return clean_tree

    def remove_item(self, item, tree):
        return [i for i in tree if item not in i]

    def check_version(self):
        try:
            response = urequests.get(self.version_url)
            if response.status_code == 200:
                json_data = json.loads(response.content)
                print(json_data)
            else:
                print(f"Failed to retrieve JSON. HTTP Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error while checking version: {e}")
        finally:
            if response:
                response.close()

                

