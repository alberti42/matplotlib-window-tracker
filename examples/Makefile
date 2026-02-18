PY ?= python3
ARGS ?=

.PHONY: help demo mwe hold recommend subplots backend-probe high-fps

help:  ## List available example targets
	@printf "%s\n" \
	"Targets:" \
	"  demo          - two windows updated in a loop (native plt.pause + hold_windows)" \
	"  mwe           - GUI -> svg save -> GUI (matplotlib-native backend switching)" \
	"  hold          - hold_windows() demo (AnyKey/Enter behavior)" \
	"  recommend     - recommended_backend() demo (select before pyplot import)" \
	"  subplots      - visual subplots(num=..., clear=...) reuse test" \
	"  backend-probe - backend switching probe (use ARGS=...)" \
	"  high-fps      - high FPS two-window demo (line.set_ydata + plt.pause)" \
	"" \
	"Examples:" \
	"  make backend-probe ARGS='--make-figure --switch svg --switch-back macosx --hold'"

demo:  ## two windows updated in a loop
	$(PY) examples/demo.py

mwe:  ## GUI -> svg save -> GUI
	$(PY) examples/matplotlib_native_mwe.py

hold:  ## hold_windows() demo
	$(PY) examples/hold_windows_demo.py

recommend:  ## recommended_backend() demo
	$(PY) examples/recommended_backend_demo.py

subplots:  ## visual subplots() reuse test
	$(PY) examples/visual_subplots_test.py

backend-probe:  ## backend switching probe (ARGS=...)
	$(PY) examples/backend_switch_probe.py $(ARGS)

high-fps:  ## high FPS two-window demo
	$(PY) examples/high_fps_two_windows.py $(ARGS)
