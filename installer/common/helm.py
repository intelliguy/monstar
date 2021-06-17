import yaml,os

class Helm:
  def __init__(self, repo, name, namespace, override):
    self.repo = repo
    self.name = name
    self.namespace = namespace
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
    self.repo.install(self.name, self.namespace, self.override)

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
    self.repo.template(self.name, self.namespace, self.override)

  def toSeperatedResources(self, targetdir='/cd', verbose=False):
    genfile=self.repo.genTemplateFile(self.name, self.namespace, self.override, verbose)

    if verbose:
      print('(DEBUG) seperate the template file')
    target = '{}/{}/'.format(targetdir, self.name)
    os.system('mkdir -p {0}; mv {1} {0}'.format(target, genfile))
    splitcmd = "awk '{f=\""+target+"/_\" NR; print $0 > f}' RS='\n---\n' "+target+genfile

    os.system(splitcmd)
    os.system('ls -al {0}; rm {0}{1}'.format(target,genfile))
    
    if verbose:
      print('(DEBUG) rename resource yaml files')
    for entry in os.scandir(target):
      print(entry)
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
        os.rename(entry, target+refinedname)
      else: 
        os.remove(entry)

  def dump(self, name, namespace, override, targetdir='/cd', verbose=False):
    yaml.dump(override, open('vo', 'w') , default_flow_style=False)
    print('[generate resource yamls {} from {} as {} in {}]'.
      format(self.chart(), self.repository(), name, namespace))

    if self.repotype == RepoType.HELMREPO:
      os.system('helm repo add monstarrepo {} | grep -i error'
        .format(self.repository()))
      os.system('mkdir -p {}/{}'.format(targetdir, name))

      if verbose:
        print('(DEBUG) gernerat a template file')

      if name.endswith('-operator'):
        os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo --include-crds  > {4}/{1}.plain.yaml'
          .format(namespace, name, self.chart(), self.version(), targetdir))
      else:
        os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo > {4}/{1}.plain.yaml'
          .format(namespace, name, self.chart(), self.version(), targetdir))

      if verbose:
        print('(DEBUG) seperate the template file')
      target = '{}/{}'.format(targetdir, name)
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

      # os.system("""awk '{f="tmp/{0}/_" NR; print $0 > f}' RS='---' tmp/{0}.plain.yaml""".format(name))
      os.system("rm {}/{}.plain.yaml".format(targetdir, name))
      os.system('helm repo rm monstarrepo | grep -i error')
    elif self.repotype == RepoType.GIT:
      if verbose:
        print('git clone -b {0} {1} temporary-clone'.format(self.versionOrReference, self.getUrl()))
      os.system('git clone -b {0} {1} temporary-clone </dev/null 2>t; cat t | grep fatal; rm t'
        .format(self.versionOrReference, self.getUrl()))

      os.system('rm -rf temporary-clone')
    else:
      print('GIT CLONE and apply')
      print(self.getUrl())
      print(self.repotype)