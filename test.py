import keyboard
keyboard.hook(lambda e: print(e.event_type, repr(e.name), e.scan_code))
keyboard.wait()