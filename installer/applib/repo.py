from enum import Enum, unique
import sys, yaml, os, time, getopt

@unique
class RepoType(Enum):
  HELMREPO=1
  GIT=2
  LOCAL=3

class Repo:
# Will Make When it's needed
  def __init__(self):
    self.list=[]

  def __init__(self, repotype, repo, chartOrPath, versionOrReference):
    self.repotype = repotype
    self.repo = repo
    self.chartOrPath = chartOrPath
    self.versionOrReference = versionOrReference

  def version(self):
    if self.repotype == RepoType.HELMREPO:
      return self.versionOrReference
    else: 
      return None

  def reference(self):
    if self.repotype == RepoType.GIT:
      return self.versionOrReference
    else: 
      return None

  def chart(self):
    if self.repotype == RepoType.HELMREPO:
      return self.chartOrPath
    else: 
      return self.chartOrPath
      # return None
  def path(self):
    if self.repotype == RepoType.GIT:
      return self.chartOrPath
    else: 
      return None

  def repository(self):
    return self.repo
    # if self.repotype == RepoType.GIT:
    #   return self.versionOrReference
    # else: 
    #   return None
  
  def getUrl(self):
    if self.repotype == RepoType.GIT and self.repo.startswith('git@'):
      if self.repo.endswith('.git'):
        return self.repo.replace(':','/').replace('git@','https://')
      else:
        return self.repo.replace(':','/').replace('git@','https://')+'.git'

    if self.repotype == RepoType.GIT:
      return self.repo
    else:
      return None

  # def getBase(self):
  #   if self.repotype == RepoType.GIT and self.repo.startswith('git@'):
  #     return self.repo.replace(':','/').replace('git@','https://')+'.git'
  #   else:
  #     return None

  def install(self, name, namespace, override, verbose=0, kubeconfig='~/.kube/config' ):
    yaml.dump(override, open('vo', 'w') , default_flow_style=False)
    print('[install {} from {} as {} in {}]'.
      format(self.chart(), self.repository(), name, namespace))

    if self.repotype == RepoType.HELMREPO:
      os.system('helm repo add monstarrepo {} | grep -i error'
        .format(self.repository()))
      os.system('helm install -n {0} {1} monstarrepo/{2} --version {3} -f vo --kubeconfig {4}'
        .format(namespace, name, self.chart(), self.version(), kubeconfig))
      os.system('helm repo rm monstarrepo | grep -i error')
    elif self.repotype == RepoType.GIT:
      # prepare repository
      if verbose > 0:
        print('(DEBUG) git clone -b {0} {1} .temporary-clone'.format(self.versionOrReference, self.repo))
        os.system('git clone -b {0} {1} .temporary-clone'
          .format(self.versionOrReference, self.repo))
      else:
        os.system('git clone -b {0} {1} .temporary-clone </dev/null 2>t; cat t | grep fatal; rm t'
          .format(self.versionOrReference, self.repo))

      # generate template file
      if verbose > 0:
        print('(DEBUG) install helm')
        print('(DEBUG) helm install -n {0} {1} .temporary-clone/{2} -f vo --kubeconfig {3}'
          .format(namespace, name, self.chartOrPath, kubeconfig))
      # helm dependency update argo-helm/charts/argo-cd 
      os.system('helm dependency update .temporary-clone/{}'.format(self.chartOrPath))

      if name.endswith('-operator'):
        os.system('helm install -n {0} {1} .temporary-clone/{2} -f vo --include-crds  --kubeconfig {3}'
          .format(namespace, name, self.chartOrPath, kubeconfig))
      else:
        os.system('helm install -n {0} {1} .temporary-clone/{2} -f vo  --kubeconfig {3}'
          .format(namespace, name, self.chartOrPath, kubeconfig))

      # clean reposiotry
      os.system('rm -rf .temporary-clone')
    else:
      print('(WARN) I CANNOT APPLY THIS. (email me - usnexp@gmail)')
      print('(WARN) '+self.getUrl())
      print('(WARN) '+self.repotype)
    return (name+'.plain.yaml')

  def template(self, name, namespace, override):
    yaml.dump(self.override, open('vo', 'w') , default_flow_style=False)
    print('[template {} from {} as {} in {}]'.
      format(self.chart(), self.repository(), name, namespace))

    if self.repotype == RepoType.HELMREPO:
      os.system('helm repo add monstarrepo {} | grep -i error'
        .format(self.repository()))
      os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo '
        .format(namespace, name, self.chart(), self.version()))
      os.system('helm repo rm monstarrepo | grep -i error')
    else:
      print('GIT CLONE and apply')

  def toSeperatedResources(self, name, namespace, override, targetdir='/cd', verbose=0):
    yaml.dump(override, open('vo', 'w') , default_flow_style=False)
    print('[generate resource yamls {} from {} as {} in {}]'.
      format(self.chart(), self.repository(), name, namespace))

    if self.repotype == RepoType.HELMREPO:
      os.system('helm repo add monstarrepo {} | grep -i error'
        .format(self.repository()))
      os.system('mkdir -p {}/{}'.format(targetdir, name))

      if verbose > 0:
        print('(DEBUG) gernerat a template file')

      if name.endswith('-operator'):
        os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo --include-crds  > {4}/{1}.plain.yaml'
          .format(namespace, name, self.chart(), self.version(), targetdir))
      else:
        os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo > {4}/{1}.plain.yaml'
          .format(namespace, name, self.chart(), self.version(), targetdir))

      if verbose > 0:
        print('(DEBUG) seperate the template file')
      target = '{}/{}'.format(targetdir, name)
      splitcmd = "awk '{f=\""+target+"/_\" NR; print $0 > f}' RS='\n---\n' "+target+".plain.yaml"
      os.system(splitcmd)
      
      if verbose > 0:
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
              if verbose > 0:
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
      if verbose > 0:
        print('git clone -b {0} {1} .temporary-clone'.format(self.versionOrReference, self.getUrl()))
      os.system('git clone -b {0} {1} .temporary-clone </dev/null 2>t; cat t | grep fatal; rm t'
        .format(self.versionOrReference, self.getUrl()))

      os.system('rm -rf .temporary-clone')
    else:
      print('(WARN) I CANNOT APPLY THIS. (email me - usnexp@gmail)')
      print('(WARN) '+self.getUrl())
      print('(WARN) '+self.repotype)

  def genTemplateFile(self, name, namespace, override, verbose=0):
    yaml.dump(override, open('vo', 'w') , default_flow_style=False)
    print('[generate resource yamls {} from {} as {} in {}]'.
      format(self.chart(), self.repository(), name, namespace))

    if self.repotype == RepoType.HELMREPO:
      # prepare repository
      if verbose > 0:
        print('(DEBUG) Register repository:: helm repo add monstarrepo {}'
          .format(self.repository()))
      os.system('helm repo add monstarrepo {} | grep -i error'
        .format(self.repository()))

      # generate template file
      if verbose > 0:
        print('(DEBUG) gernerat a template file')
      if name.endswith('-operator'):
        os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo --include-crds  > {1}.plain.yaml'
          .format(namespace, name, self.chart(), self.version()))
      else:
        os.system('helm template -n {0} {1} monstarrepo/{2} --version {3} -f vo > {1}.plain.yaml'
          .format(namespace, name, self.chart(), self.version()))

      # clean reposiotry
      os.system('helm repo rm monstarrepo | grep -i error')
    elif self.repotype == RepoType.GIT:
      # prepare repository
      if verbose > 0:
        print('(DEBUG) git clone -b {0} {1} .temporary-clone'.format(self.versionOrReference, self.getUrl()))
        os.system('git clone -b {0} {1} .temporary-clone'
          .format(self.reference(), self.getUrl()))
        if verbose > 2:
          print('(DEBUG) Cloned dir :')
          os.system('ls -al .temporary-clone')
      else:
        os.system('git clone -b {0} {1} .temporary-clone </dev/null 2>t; cat t | grep fatal; rm t'
          .format(self.versionOrReference, self.getUrl()))

      os.system('helm dependency update .temporary-clone/{}'.format(self.path()))
      # generate template file
      if verbose > 0:
        print('(DEBUG) gernerat a template file')
        print('(DEBUG) helm template -n {0} {1} .temporary-clone/{2} -f vo > {1}.plain.yaml'
          .format(namespace, name, self.path()))
      if name.endswith('-operator'):
        os.system('helm template -n {0} {1} .temporary-clone/{2} -f vo --include-crds  > {1}.plain.yaml'
          .format(namespace, name, self.path()))
      else:
        os.system('helm template -n {0} {1} .temporary-clone/{2} -f vo > {1}.plain.yaml'
          .format(namespace, name, self.path()))

      # clean reposiotry
      os.system('rm -rf .temporary-clone')
      # os.system('mv .temporary-clone '+name)
    else:
      print('(WARN) I CANNOT APPLY THIS. (email me - usnexp@gmail)')
      print('(WARN) '+self.getUrl())
      print('(WARN) '+self.repotype)
    return (name+'.plain.yaml')