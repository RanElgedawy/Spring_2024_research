def main():
  with open("complexity.txt", "r") as f:
    data = f.readlines()
  
  tasks = [[[ [] for _ in range(4)] for _ in range(6)] for _ in range(9)]
  t = -1
  p = 0
  m = 0
  a = 0

  # split data
  for line in data:
    l = line.strip()

    # skip lines
    if l == "task.py": continue

    # increment tasks
    elif l[0:3] == "# T": 
      t += 1
      p = 0
      m = 0
      a = 0

    # increment persona
    elif l == "## Persona 1": continue
    elif l == "## Persona 2": 
      p = 1
      m = 0
      a = 0

    # increment model
    elif l == "### GPT-4": continue 
    elif l == "### GPT-3.5": 
      m = 1
      a = 0
    elif l == "### Bard":
      m = 2
      a = 0
    elif l == "### Gemini": 
      m = 2
      a = 0

    # increment which test we did
    elif l == "#### Cyclomatic Complexity test": continue
    elif l == "#### Maintainability Index score (multi-line comments)": a = 1
    elif l == "#### raw metrics": a = 2
    elif l == "#### Halstead complexity metrics (file)": a = 3

    # store lines
    else: tasks[t][p*3+m][a].append(l)
  
  # analyze complexity first
  complex_results = [[] for _ in range(9)]


  for i in range(9):
    for j in range(2):
      for k in range(3):
        # print(f"Task {i+1}, Persona {j+1}, Model {k+1}:")
        for line in tasks[i][j*3+k][0]:
          print(line)
          if "blocks (classes, functions, methods) analyzed." in line: complex_results[i].append(int(line[0]))
          elif "Average complexity:" in line: complex_results[i].append(line.split(': ')[-1])
          if line.strip() == "NA": 
            complex_results[i].append(0)
            complex_results[i].append(0)
        # print()
  
  print("Tasks")
  for line in complex_results: 
    print(line)
 
  print("\nCyclomatic Complexity tests")

  b = [0,0,0]
  s = [0,0,0]
  pb = [0,0]
  ps = [0,0]
  for i in range(9):
    task = []
    persona_b = [0,0]
    persona_s = [0,0]
    for j in (0,2,4,6,8,10):
      # print(f"m:{(j//2)%4} p:{j//8}")
      # Skip 0s
      if complex_results[i][j] == 0: 
        # Per model
        task.append(task[len(task)-8])
        task.append(float(task[len(task)-8]))
        b[(j//2)%3] += task[len(task)-10]
        s[(j//2)%3] += float(task[len(task)-9])

        # Per persona
        persona_b[j//6] += .5 * persona_b[j//6]
        persona_s[j//6] += .5 * persona_s[j//6]
        pb[j//6] += .25 * persona_b[j//6]
        ps[j//6] += .25 * persona_s[j//6]
        continue
      
      # Per model
      b[(j//2)%3] += complex_results[i][j]
      s[(j//2)%3] += float(complex_results[i][j+1].split('(')[1].split(')')[0])
      task.append(complex_results[i][j])
      task.append(float(complex_results[i][j+1].split('(')[1].split(')')[0]))

      # Per persona
      persona_b[j//6] += complex_results[i][j]
      persona_s[j//6] += float(complex_results[i][j+1].split('(')[1].split(')')[0])
      pb[j//6] += complex_results[i][j]
      ps[j//6] += float(complex_results[i][j+1].split('(')[1].split(')')[0])
    print(f"Task {i+1} ", end="")
    for k in (2,0,4):
      print(f"& {(task[k]+task[k+6])/2}; \color{{blue}}{round((task[k+1]+task[k+1+6])/2,2)} ", end="")
    print(f"& {round(persona_b[0]/3,2)}; \color{{blue}}{round(persona_s[0]/3,2)} & {round(persona_b[1]/3,2)}; \color{{blue}}{round(persona_s[1]/3,2)} \\\\")
  print("\\hline")
  print(f"Average & {round(b[1]/9/2,2)}; \color{{blue}}{round(s[1]/9/2,2)} & {round(b[0]/9/2,2)}; \color{{blue}}{round(s[0]/9/2,2)} & {round(b[2]/9/2,2)}; \color{{blue}}{round(s[2]/9/2,2)} & {round(pb[0]/9/3,2)}; \color{{blue}}{round(ps[0]/9/3,2)} & {round(pb[1]/9/3,2)}; \color{{blue}}{round(ps[1]/9/3,2)} \\\\")

  # Then we look at things like LoC and comments
  print("\n\nLoC and comments\n")
  raw = [[] for _ in range(9)]

  for i in range(9):
    for j in range(2):
      for k in range(3):
        # print(f"Task {i+1}, Persona {j+1}, Model {k+1}:")

        # Fill in NA 
        if tasks[i][j*3+k] == [['NA'], [], [], []]:
          print(f"Task {i+1}, Persona {j+1}, Model {k+1} is NA")
          if j == 1:
            raw[i].append(raw[i][k*2])
            raw[i].append(raw[i][k*2+1])
          continue

        f = 0
        for line in tasks[i][j*3+k][2]:
          if line == "** Total **": f=1
          elif not f: continue
          # print(line)
          if "LOC:" in line and "SLOC" not in line and "LLOC" not in line: raw[i].append(int(line.split(': ')[1]))
          elif "(C % L):" in line: 
            raw[i].append(int(line.split(': ')[1].split('%')[0]))
            f = 0
        # print()

  for l in raw:
    print(l)
  print()

  l = [0,0,0]
  c = [0,0,0]
  pl = [0,0]
  pc = [0,0]
  for i in range(9):
    code = []
    persona_l = [0,0]
    persona_c = [0,0]
    for j in (0,2,4,6,8,10):
      l[(j//2)%3] += int(raw[i][j])
      c[(j//2)%3] += int(raw[i][j+1])
      
      pl[j//6] += int(raw[i][j])
      pc[j//6] += int(raw[i][j+1])

      code.append(int(raw[i][j]))
      code.append(int(raw[i][j+1]))

      persona_l[j//6] += int(raw[i][j])
      persona_c[j//6] += int(raw[i][j+1])

    print(f"Task {i+1} ", end="")
    for k in (2,0,4):
      print(f"& {(code[k]+code[k+6])/2}; \color{{blue}}{round((code[k+1]+code[k+1+6])/2,2)} ", end="")
    print(f"& {round(persona_l[0]/3,2)}; \color{{blue}}{round(persona_c[0]/3,2)} & {round(persona_l[1]/3,2)}; \color{{blue}}{round(persona_c[1]/3,2)} \\\\")
  print("\\hline")
  print(f"Average & {round(l[1]/9/2,2)}; \color{{blue}}{round(c[1]/9/2,2)} & {round(l[0]/9/2,2)}; \color{{blue}}{round(c[0]/9/2,2)} & {round(l[2]/9/2,2)}; \color{{blue}}{round(c[2]/9/2,2)} & {round(pl[0]/9/3,2)}; \color{{blue}}{round(pc[0]/9/3,2)} & {round(pl[1]/9/3,2)}; \color{{blue}}{round(pc[1]/9/3,2)} \\\\")

  # Num external libraries
  print("\nExternal library calls")

  ## Order is [GPT-4o P1, GPT3.5 P1, Gemini P1, GPT-4o P2, GPT-3.5 P2, Gemini P2]
  # -1 is no output (Gemini)
  # rows are tasks, columns are models/personas
  ext_libs = [
    [6, 3, 0, 3, 2, 3],
    [2, 1, 2, 1, 2, 3],
    [3, 1, 3, 2, 1, 1],
    [1, 1, 1, 1, 1, 0],
    [2, 1, 2, 5, 1, 4],
    [2, 1, 0, 4, 3, 1],
    [3, 1, 1, 1, 1, 3],
    [0, 1, 2, 0, 1, 6],
    [1, 1, 1, 4, 1, 1],
  ]

  persona_totals = [[],[]]
  model_totals = [[[],[]],[[],[]],[[],[]]]

  for i, task in enumerate(ext_libs):
    print(f"Task {i+1} ", end="")
    tmp_personas = [[],[]]
    for j in range(3):
      x = task[j] if task[j] != -1 else "NA"
      y = task[j+3] if task[j+3] != -1 else "NA"

      persona_totals[0].append(x) if x != "NA" else persona_totals[0]
      persona_totals[1].append(y) if y != "NA" else persona_totals[1]
      
      model_totals[j][0].append(x) if x != "NA" else model_totals[j][0]
      model_totals[j][1].append(y) if y != "NA" else model_totals[j][1]

      tmp_personas[0].append(x) if x != "NA" else tmp_personas[0]
      tmp_personas[1].append(y) if y != "NA" else tmp_personas[1]

      print(f"& {x}; \color{{blue}}{y} ", end="")
    print(f"& {round(sum(tmp_personas[0])/len(tmp_personas[0]),2)} & {round(sum(tmp_personas[1])/len(tmp_personas[1]),2)} \\\\")
  print("\\hline")

  for i in range(3):
    model_totals[i] = [round(sum(model_totals[i][0])/len(model_totals[i][0]),2), round(sum(model_totals[i][1])/len(model_totals[i][1]),2)]
  print("Average ", end="")
  for i in range(3):
    print(f"& {model_totals[i][0]}; \color{{blue}}{model_totals[i][1]} ", end="")
  print(f"& {round(sum(persona_totals[0])/len(persona_totals[0]),2)} & {round(sum(persona_totals[1])/len(persona_totals[1]),2)} \\\\")

if __name__ == '__main__':
  main()