import matplotlib.pyplot as plt
import numpy as np

def counts(data):
  # Create a new array for each model
  a_data = data[:, [0,2]]
  b_data = data[:, [1,3]]
  # c_data = data[:, [2,6]]
  # d_data = data[:, [3,7]]

  # Count occurrences of 1, 2, and 3 for each model
  counts_a = [0,0,0]
  for i in a_data:
    for j in i:
       if j == 1: counts_a[0] += 1
       elif j == 2: counts_a[1] += 1
       elif j == 3: counts_a[2] += 1
  
  counts_b = [0,0,0]
  for i in b_data:
    for j in i:
       if j == 1: counts_b[0] += 1
       elif j == 2: counts_b[1] += 1
       elif j == 3: counts_b[2] += 1
    '''
  counts_c = [0,0, 0]
  for i in c_data:
    for j in i:
       if j == 1: counts_c[0] += 1
       elif j == 2: counts_c[1] += 1
       elif j == 3: counts_c[2] += 1

  counts_d = [0,0,0]
  for i in d_data:
    for j in i:
       if j == 1: counts_d[0] += 1
       elif j == 2: counts_d[1] += 1
       elif j == 3: counts_d[2] += 1
  '''
  results = {
    # 'GPT-3.5': counts_b,
    'GPT-4o': counts_a,
    # 'Bard': counts_c, # add back later when recreating graph
    'Gemini': counts_b
  }

  return results

def labels(results):
  labels = list(results.keys())
  data = np.array(list(results.values()))
  data_cum = data.cumsum(axis=1)
  return labels, data, data_cum

def main():
  syntax    = [2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 3, 3, 2, 3, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 3, 3, 2, 2, 2, 2, 2]
  function  = [1, 1, 3, 3, 3, 1, 1, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 1, 3, 2, 1, 3, 1, 3, 3, 3, 3, 1, 3, 3, 3]
  # semantics = [1, 1, 3, 3, 1, 1, 1, 3, 1, 1, 2, 1, 1, 1, 2, 3, 3, 2, 3, 3, 1, 2, 2, 3, 1, 1, 1, 2, 3, 2, 2, 2, 1, 2, 2, 1, 1, 1, 2, 1, 3, 3, 2, 1, 2, 3, 3, 3, 3, 2, 3, 1, 3, 3, 2, 3, 2, 1, 2, 1, 1, 2, 2, 3, 3, 3, 2, 2, 3, 3, 2, 3]

  # Reshape the array
  data_s = np.array(syntax).reshape((9, 4))
  data_f = np.array(function).reshape((9, 4))
  # data_se = np.array(semantics).reshape((9, 8))
  category_names = ["1 (identical)", "2 (similar)", "3 (different)"]

  labels_s, data_s, data_s_cum, = labels(counts(data_s))
  _, data_f, data_f_cum, = labels(counts(data_f))
  # _, data_se, data_se_cum, = labels(counts(data_se))

  _, ax = plt.subplots(figsize=(12, 7))
  ax.invert_yaxis()
  ax.set_xlim(0, np.sum(data_s, axis=1).max())

  bar_width = 0.2  # Width of each bar
  bar_positions_s = np.arange(len(labels_s))
  bar_positions_f = bar_positions_s + bar_width
  # bar_positions_se = bar_positions_f + bar_width

  # Plot syntax
  category_colors = ["#236EC3", "#E1E1E1", "#C32314"]
  for i, (colname, color) in enumerate(zip(category_names, category_colors)):
    widths = data_s[:, i]
    starts = data_s_cum[:, i] - widths
    rects = ax.barh(bar_positions_s, widths, left=starts, height=bar_width,
                    label=f"{colname} (Syntax)", color=color)
    ax.bar_label(rects, label_type='center', color='black', fontsize=16)

  # Plot function
  category_colors = ["#5ab4ac", "#dfc283", "#d8a539"]
  for i, (colname, color) in enumerate(zip(category_names, category_colors)):
    widths = data_f[:, i]
    starts = data_f_cum[:, i] - widths
    rects = ax.barh(bar_positions_f, widths, left=starts, height=bar_width,
                    label=f"{colname} (Functionality)", color=color)
    ax.bar_label(rects, label_type='center', color='black', fontsize=16)

    '''
  # Plot semantics
  category_colors = ["#C55D00", "#808080", "#5F3B3B"]
  for i, (colname, color) in enumerate(zip(category_names, category_colors)):
    widths = data_se[:, i]
    starts = data_se_cum[:, i] - widths
    rects = ax.barh(bar_positions_se, widths, left=starts, height=bar_width,
                    label=f"{colname} (Semantics)", color=color)
    ax.bar_label(rects, label_type='center', color='black', fontsize=16)
    '''
  ax.set_yticks(bar_positions_f)
  ax.set_yticklabels(["GPT-4o", "Gemini"], fontsize=16) #"GPT-3.5", "GPT-4", "Bard", "Gemini"], fontsize=16)
  ax.set_xticklabels(ax.get_xticks().astype(int), fontsize=16)  
  ax.set_xlabel('Count', fontsize=18)
  ax.set_ylabel('Model', fontsize=18)
  ax.set_title('Syntax and Functionality Consistency by Model', fontsize=22)
  # ax.legend()

  plt.savefig('consistencyTest2.pdf')

  # Create a legend figure
  legend_fig = plt.figure(figsize=(6, 2))
  ax_legend = legend_fig.add_subplot(111)
  ax_legend.axis('off')
  legend = ax_legend.legend(*ax.get_legend_handles_labels(), loc='center', ncol=2)

  # Save the legend figure
  legend_fig.savefig('legend2.pdf', bbox_inches='tight')

  plt.tight_layout()
  plt.savefig('Grouped.pdf')

if __name__ == '__main__':
  main()