from PIL import Image, ImageDraw, ImageFont

# -------------------------- 基础配置 --------------------------
WIDTH = 675
PADDING = 20
NICK_SIZE = 14
TEXT_SIZE = 16
BUBBLE_RADIUS = 12
BUBBLE_PAD = 14
LINE_SPACE = 6
MSG_GAP = 18

BG_COLOR = (245, 245, 245)
NICK_COLOR = (184, 184, 184)
BUBBLE_COLOR = (255, 255, 255)
TEXT_COLOR = (35, 35, 35)

# 字体
try:
    font_nick = ImageFont.truetype("msyh.ttc", NICK_SIZE)
    font_text = ImageFont.truetype("msyh.ttc", TEXT_SIZE)
except:
    font_nick = ImageFont.load_default(size=NICK_SIZE)
    font_text = ImageFont.load_default(size=TEXT_SIZE)

# -------------------------- 消息列表（改为二维数组）--------------------------
# 格式：[["昵称1", "文本内容1"], ["昵称2", "文本内容2"], ...]


# -------------------------- 文本换行工具 --------------------------
def wrap_text(text, font, max_width):
    lines = []
    if not text:
        return lines
    words = list(text)
    current_line = ""
    for w in words:
        test = current_line + w
        wd = font.getlength(test)
        if wd <= max_width:
            current_line = test
        else:
            lines.append(current_line)
            current_line = w
    if current_line:
        lines.append(current_line)
    return lines

# -------------------------- 生成 --------------------------
def generate_chat_image(messages, save_path="chat.png"):
    temp_im = Image.new("RGB", (1, 1), BG_COLOR)
    temp_draw = ImageDraw.Draw(temp_im)

    max_text_w = WIDTH - PADDING * 4
    y = PADDING
    blocks = []

    # 关键修改：遍历二维数组，取[0]为昵称，[1]为文本
    for msg in messages:
        nick = msg[0]  # 数组第一个元素是昵称
        text = msg[1]  # 数组第二个元素是文本

        nick_w = temp_draw.textlength(nick, font=font_nick)
        lines = wrap_text(text, font_text, max_text_w)

        line_heights = []
        total_text_h = 0
        for line in lines:
            _, _, _, th = font_text.getbbox(line)
            line_heights.append(th)
            total_text_h += th
        if len(lines) > 1:
            total_text_h += (len(lines)-1) * LINE_SPACE

        text_w = max(temp_draw.textlength(line, font=font_text) for line in lines) if lines else 0
        bubble_w = max(nick_w, text_w) + BUBBLE_PAD * 2
        bubble_h = total_text_h + BUBBLE_PAD * 2
        block_h = NICK_SIZE + 6 + bubble_h

        blocks.append({
            "nick": nick,
            "lines": lines,
            "nick_w": nick_w,
            "bubble_w": bubble_w,
            "bubble_h": bubble_h,
            "y": y
        })
        y += block_h + MSG_GAP

    # 正式画布
    img_h = y + PADDING
    im = Image.new("RGB", (WIDTH, img_h), BG_COLOR)
    draw = ImageDraw.Draw(im)

    for b in blocks:
        # 昵称
        draw.text((PADDING, b["y"]), b["nick"], fill=NICK_COLOR, font=font_nick)

        # 气泡
        by = b["y"] + NICK_SIZE + 4
        bx1 = PADDING
        bx2 = PADDING + b["bubble_w"]
        by1 = by
        by2 = by + b["bubble_h"]
        draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=BUBBLE_RADIUS, fill=BUBBLE_COLOR)

        # 文字（逐行）
        ty = by + BUBBLE_PAD
        for line in b["lines"]:
            draw.text((bx1 + BUBBLE_PAD, ty), line, fill=TEXT_COLOR, font=font_text)
            _, _, _, th = font_text.getbbox(line)
            ty += th + LINE_SPACE

    im.save(save_path)
    print("✅ 图片已生成:", save_path)

if __name__ == "__main__":
    messages = [
    ["海星来来", "我昨晚做梦梦见理发师给我整了个沛之的发型，我照了下镜子觉得还不如我现在的，然后我就被吓醒了。"],
    ["海星来来", "发型这个事儿真的还是得看人来做设计，不是所有好看的发型都适合自己。"],
    ["小明", "哈哈哈哈太真实了，有时候真的是看脸，我也踩过很多雷。"],
]
    generate_chat_image(messages)