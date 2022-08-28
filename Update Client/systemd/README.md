# systemd units

Place both unit files at ~/.config/systemd/user/

## Timer
Configure the `OnCalendar` to taste

## Service

* Add the appropriate command line args to the `ExecStart` command.
* Use -v to add more logging (**WILL LOG CREDENTIALS**)
* Recommend you keep the -t flag to reduce log emits
