"""Small Tk boundary doubles; production handlers and threads stay real."""


class FakeVariable:
    """Mimic StringVar's value and write notifications."""

    def __init__(self, _master=None, value=""):
        self.value = value
        self.callbacks = []

    def get(self):
        """Read current input."""
        return self.value

    def set(self, value):
        """Notify input observers on writes, as Tk does."""
        self.value = value
        for callback in self.callbacks:
            callback("", "", "write")

    def trace_add(self, _mode, callback):
        """Register a write observer."""
        self.callbacks.append(callback)
        return callback

    def trace_remove(self, _mode, callback):
        """Release an observer, matching StringVar's lifecycle contract."""
        self.callbacks.remove(callback)


class FakeWidget:
    """Record visible text, state and layout at the widget boundary."""

    def __init__(self, parent=None, **options):
        self.options = options
        self.bindings = {}
        self.destroyed = False
        self.children = []
        if parent is not None:
            parent.children.append(self)

    def config(self, **options):
        """Apply UI changes, rejecting stale writes."""
        assert not self.destroyed, "updated destroyed widget"
        self.options.update(options)

    configure = config

    def __getitem__(self, key):
        return self.options[key]

    def __setitem__(self, key, value):
        self.config(**{key: value})

    def get(self, *_indices):
        """Read an entry or combobox."""
        variable = self.options.get("textvariable")
        return variable.get() if variable else self.options.get("text", "")

    def delete(self, *_indices):
        """Clear a display or Entry, including its linked StringVar."""
        variable = self.options.get("textvariable")
        if variable:
            variable.set("")
        else:
            self.options["text"] = ""

    def insert(self, _index, text):
        """Populate a cleared display or Entry, notifying variable observers."""
        variable = self.options.get("textvariable")
        if variable:
            variable.set(text)
        else:
            self.options["text"] = text

    def yview(self, *_args):
        """Scrollbar target; native scrolling is covered by the Tk regression."""

    def set(self, *_args):
        """Scrollbar update boundary."""

    def bind(self, event, callback):
        """Remember event handlers without rendering Tk."""
        self.bindings[event] = callback

    def pack(self, **_options):
        """Layout is tested through the real UI smoke check."""

    def destroy(self):
        """Make any subsequent update fail."""
        self.destroyed = True


class FakeParent:
    """Deterministic Tk scheduler: tests explicitly pump queued callbacks."""

    def __init__(self):
        self.children = []
        self.pending = {}
        self.next_id = 0

    def after(self, _delay, callback):
        """Queue callbacks without invoking them on the worker thread."""
        self.next_id += 1
        self.pending[self.next_id] = callback
        return self.next_id

    def after_cancel(self, callback_id):
        """Discard a mode's scheduled callback."""
        self.pending.pop(callback_id, None)

    def pump(self):
        """Run one batch of scheduled events on the test's main thread."""
        callbacks = list(self.pending.values())
        self.pending.clear()
        for callback in callbacks:
            callback()

    def winfo_children(self):
        """Return widgets for controller teardown."""
        return self.children


def patch_verify_widgets(monkeypatch, module):
    """Replace only Tk construction; verification and hashing remain real."""
    monkeypatch.setattr(module.tk, "StringVar", FakeVariable)
    for name in ("Button", "Label", "Entry", "Frame", "Text"):
        monkeypatch.setattr(module.tk, name, FakeWidget)
    if hasattr(module, "ttk"):
        for name in ("Combobox", "Progressbar", "Scrollbar"):
            monkeypatch.setattr(module.ttk, name, FakeWidget)
