while true do
  term.setCursorPos(1,1)
  term.clear()
  term.write(textutils.formatTime(os.time(), true))
  sleep(1)
end
