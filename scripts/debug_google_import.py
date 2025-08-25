import importlib,sys,traceback
try:
    import google
    print('google.__file__=', getattr(google, '__file__', None))
    import google.auth as ga
    print('google.auth.__file__=', getattr(ga, '__file__', None))
    print('has environment_vars=', hasattr(ga, 'environment_vars'))
    print('dir(google.auth) sample =', list(dir(ga))[:200])
except Exception:
    print('IMPORT ERROR')
    traceback.print_exc()
