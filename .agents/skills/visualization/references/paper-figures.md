# 可直接入论文的图：绘图代码与版面协同

绘图前先确定论文模板的正文可用宽度、图片放在正文还是附录，以及这张图要证明的一个具体结论。图不是装饰：它须与原始数据、处理版本、评价划分和正文解释对应。2026 年研究生数模竞赛的格式以当届官方附件 2、3 为准；这里的尺寸和字体是可调起点，不是官方规定。

## 图的取舍与视觉层次

- 正文优先放流程/机制总览、关键方法对照、核心结果和必要的失败或稳健性图。八张结构相同的曲线通常比不上两张可读的比较图加附录中的完整曲线；但分面过密时应拆开，而非缩成看不清的一页。
- 同一比较中的面板保持一致的坐标范围、颜色编码、时间零点和样本口径；不同量纲不要强行共轴。比较曲线时用颜色加线型/标记双重区分，保证灰度打印仍可辨。阴影须标明是置信区间、分位区间还是变异范围，且确有计算依据。
- 图内只保留阅读必需的信息：坐标名称与单位、适度刻度、简短图例和 (a)(b)… 面板标识。长标题、方法细节和样本说明放图题；多余网格、3D 效果、渐变背景和重复图例会压缩数据区域。
- 在最终插入宽度下检查数字和文字；优先调整绘图代码中的画布比例、标签、图例与面板布局，不靠在 Word/LaTeX 中把大图缩到难以阅读。表格更适合精确比较数值，曲线更适合形状与趋势，不把同一结果机械重复成表和图。

## 代码输出契约

1. 从最终版式的正文宽度反推 `figsize`，保持纵横比，依据面板数量决定整栏图或较宽图；常见起点是可用宽度的 1.0 倍和高度约为宽度的 0.55–0.7 倍，但以实际可读性调整。轴标签、刻度和图例在插入后的尺寸应能读清。
2. 用统一的绘图样式控制字体、线宽、颜色和小数位；中文字体必须在运行环境中存在，不能只设字体名就假定导出 PDF 正常。若颜色有语义，整个论文保持一致；对打印版检查灰度差异。
3. Matplotlib 多面板优先用 `layout="constrained"` 处理标签、图例和色条的占位，必要时手动微调；不要再叠加 `tight_layout()`，后者会关闭 constrained layout。详见 [Matplotlib 官方布局说明](https://matplotlib.org/stable/users/explain/axes/constrainedlayout_guide.html)。
4. 用代码一次生成可编辑/可放大的 PDF 或 SVG，以及适合 Word 的清晰 PNG（通常从目标尺寸以 300 dpi 起步）；不要把屏幕截图、网页缩略图或低分辨率 JPEG 当论文主图。Matplotlib 的 `savefig` 支持格式和 dpi 参数，见[官方说明](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)。矢量图内密集栅格或大量散点可有选择地栅格化，文字与线条仍保持清晰。
5. 每张图的生成代码可重跑，文件名含图义或稳定 ID；`figure_manifest.json` 记录输入文件/哈希、处理版本、运行命令、图的面板含义、图用于哪一问，以及输出 PDF/PNG 的路径。只记录实际生成的文件。

Matplotlib 示例应按本机字体和模板宽度调整，不是必须照抄的全局样式：

```python
from matplotlib import pyplot as plt
from matplotlib import rc_context

text_width_cm = 15.0  # 从实际论文模板测量，不能把示例值当官方规定
width_in = text_width_cm / 2.54
style = {
    "font.sans-serif": ["Microsoft YaHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "pdf.fonttype": 42,
}
with rc_context(style):
    fig, ax = plt.subplots(figsize=(width_in, width_in * 0.6), layout="constrained")
    # ax.plot(x, y, label="实际结果")  # 用真实数据填充，并设置单位、图例与需要的比较项
    ax.set_xlabel("时间 / s")
    ax.set_ylabel("信号 / 实际单位")
    if ax.get_legend_handles_labels()[0]:
        ax.legend()
    fig.savefig("result.pdf")
    fig.savefig("result.png", dpi=300)
    plt.close(fig)
```

## 插入与一次实际检查

图放在首次讨论附近，正文先引出比较目标，再给编号图题，图后用文字解释“看到什么、对应什么结论、有什么限制”。多面板图题解释每个面板和颜色/阴影的含义。Word/LaTeX 插入时保持纵横比与模板边距，让图题和图尽量同页；避免一页连续堆几张大图而没有解释。

在导出的最终文稿 PDF 中按实际阅读尺寸检查一次：是否有字体缺字、裁切、图例压线、数字过小、低清晰度、颜色难辨、图题与图分离。发现问题回到绘图代码调整，并复查受影响图；无需反复全书目视审查。
