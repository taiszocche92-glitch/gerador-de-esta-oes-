import traceback
try:
    import firebase_admin
    print('firebase_admin.__file__ =', getattr(firebase_admin,'__file__',None))
    print('firebase_admin.__package__ =', getattr(firebase_admin,'__package__',None))
    print('firebase_admin modules sample =', [m for m in dir(firebase_admin) if not m.startswith('_')][:50])
except Exception as e:
    print('IMPORT ERROR')
    traceback.print_exc()
