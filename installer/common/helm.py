import yaml,os

class Helm:
  def __init__(self, repo, chart, name, namespace, version, override):
    self.repo = repo
    self.chart = chart
    self.name = name
    self.namespace = namespace
    self.version = version
    self.override = override

  def checkPrerequisitions(self):
  #  stream = os.popen('kubectl get ns {}'
  #     .format(self.namespace))
  #   try:
  #     return stream.read().rsplit("STATUS:")[1].split()[0].strip()
  #   except IndexError as exc:
  #     return None
    return True

  def autoApplyPrerequisitions(self):
    return True

  def install(self):
    yaml.dump(self.override, open('vo', 'w') , default_flow_style=False)
    print('[install {} from {} as {} in {}]'.
      format(self.chart, self.repo, self.name, self.namespace))
    os.system('helm repo add monstarrepo {} | grep -i error'
      .format(self.repo))
    os.system('helm install -n {0} {1} monstarrepo/{2} --version {3} -f vo'
      .format(self.namespace, self.name, self.chart, self.version))
    os.system('helm repo rm monstarrepo | grep -i error')

  def uninstall(self):
    print('helm delete -n {} {} | grep status'
      .format(self.namespace, self.name))

  def getStatus(self):
    stream = os.popen('helm status -n {} {}'
      .format(self.namespace, self.name))
    try:
      return stream.read().rsplit("STATUS:")[1].split()[0].strip()
    except IndexError as exc:
      return None

  def getStatusfull(self):
    os.system('helm status -n {} {}'
      .format(self.namespace, self.name))

  def template(self):
    yaml.dump(self.override, open('vo', 'w') , default_flow_style=False)
    print('[template {} from {} as {} in {}]'.
      format(self.chart, self.repo, self.name, self.namespace))
    os.system('helm repo add monstarrepo {} | grep -i error'
      .format(self.repo))
    os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo '
      .format(self.namespace, self.name, self.chart, self.version))
    os.system('helm repo rm monstarrepo | grep -i error')

  def toSeperatedResources(self, targetdir='/cd', verbose=False):
    yaml.dump(self.override, open('vo', 'w') , default_flow_style=False)
    print('[generate resource yamls {} from {} as {} in {}]'.
      format(self.chart, self.repo, self.name, self.namespace))
    os.system('helm repo add monstarrepo {} | grep -i error'
      .format(self.repo))
    os.system('mkdir -p {}/{}'.format(targetdir, self.name))

    if verbose:
      print('(DEBUG) gernerat a template file')

    if self.name.endswith('-operator'):
      os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo --include-crds  > {4}/{1}.plain.yaml'
        .format(self.namespace, self.name, self.chart, self.version, targetdir))
    else:
      os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo > {4}/{1}.plain.yaml'
        .format(self.namespace, self.name, self.chart, self.version, targetdir))

    if verbose:
      print('(DEBUG) seperate the template file')
    target = '{}/{}'.format(targetdir, self.name)
    splitcmd = "awk '{f=\""+target+"/_\" NR; print $0 > f}' RS='\n---\n' "+target+".plain.yaml"
    os.system(splitcmd)
    
    if verbose:
      print('(DEBUG) rename resource yaml files')
    for entry in os.scandir(target):
      refinedname =''
      with open(entry, 'r') as stream:
        try:
          parsed = yaml.safe_load(stream)
          refinedname = '{}_{}.yaml'.format(parsed['kind'],parsed['metadata']['name'])
        except yaml.YAMLError as exc:
          print('(WARN)',exc,":::", parsed)
        except TypeError as exc:
          if os.path.getsize(entry)>80:
            print('(WARN)',exc,":::", parsed)
            if verbose:
              print("(DEBUG) Contents in the file :", entry.name)
              print(stream.readlines())
      if (refinedname!=''):
        os.rename(entry, target+'/'+refinedname)
      else: 
        os.remove(entry)

    # os.system("""awk '{f="tmp/{0}/_" NR; print $0 > f}' RS='---' tmp/{0}.plain.yaml""".format(self.name))
    os.system("rm {}/{}.plain.yaml".format(targetdir, self.name))
    os.system('helm repo rm monstarrepo | grep -i error')

