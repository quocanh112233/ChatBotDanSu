
import os
import re
from pypdf import PdfReader

# Đường dẫn file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
FILE_PATH = os.path.join(DATA_DIR, "LuatDanSu2015.pdf")

def read_pdf(file_path):
    print(f"--- Đang đọc file: {os.path.basename(file_path)} ---")
    if not os.path.exists(file_path):
        print(f"LỖI: Không tìm thấy file {file_path}")
        return ""
    
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text



def clean_text(text):
    # 1. Chuẩn hóa khoảng trắng cơ bản
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 2. Xử lý xuống dòng (Smart Merge)
    # Giữ lại xuống dòng trước các từ khóa cấu trúc: Phần, Chương, Mục, Điều
    text = re.sub(r'\n\s+', '\n', text)
    
    # Regex lookahead để bảo vệ dòng header
    # Protect: Điều X, Chương X, Phần X, Mục X
    header_pattern = r'Điều \d+|Chương (?=[MDCLXVI])|Phần (?=thứ)|Mục \d+'
    
    # Merge dòng bình thường, nhưng giữ lại \n nếu dòng tiếp theo là Header
    smart_merge_pattern = r'\n(?!(' + header_pattern + r'))'
    text = re.sub(smart_merge_pattern, ' ', text, flags=re.IGNORECASE)
    
    # 3. Clean lại lần cuối
    text = re.sub(r'\s+', ' ', text).strip()
    return text.strip()

def chunk_by_article(text):
    """
    Chia văn bản thành các chunk có kèm thông tin ngữ cảnh (Phần -> Chương -> Mục).
    """
    # Bước 1: Tái tạo cấu trúc dòng
    # Thêm \n trước các Header chính để dễ xử lý (nếu clean_text đã lỡ xóa)
    patterns = [
        (r'(Phần thứ [a-zA-Zăâêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵđ\s]+)', r'\n\1'),
        (r'(Chương [IVXLCDM]+)', r'\n\1'),
        (r'(Mục \d+)', r'\n\1'),
        (r'(Điều \d+[\.\s])', r'\n\1')
    ]
    
    temp_text = text
    for p, r in patterns:
        temp_text = re.sub(p, r, temp_text, flags=re.IGNORECASE)
    
    lines = temp_text.split('\n')
    
    final_chunks = []
    
    # Context State
    current_part = ""
    current_chapter = ""
    current_section = ""
    
    current_article_lines = []
    
    # Patterns for Header Detection
    p_part = re.compile(r'^Phần thứ', re.IGNORECASE)
    p_chap = re.compile(r'^Chương [IVXLCDM]+', re.IGNORECASE)
    p_sec = re.compile(r'^Mục \d+', re.IGNORECASE)
    p_art = re.compile(r'^Điều \d+', re.IGNORECASE)
    
    invalid_prefixes = ["tại", "của", "theo", "khoản", "điểm", "mục", "trong", "với", "và", "hoặc"]

    def save_current_article():
        if current_article_lines:
            # Join text
            content = " ".join(current_article_lines).strip()
            
            # Extract Article ID for context injection check
            # (Chỉ là check nhẹ để đảm bảo nó là Điều luật thật)
            if len(content) > 20: 
                # Build Context String
                context_str = []
                if current_part: context_str.append(current_part)
                if current_chapter: context_str.append(current_chapter)
                if current_section: context_str.append(current_section)
                
                full_context = " - ".join(context_str)
                if full_context:
                    # Inject Context to top
                    content = f"[Thuộc {full_context}]\n{content}"
                
                final_chunks.append(content)

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check Headers
        if p_part.match(line):
            save_current_article() # Save previous article if exists
            current_article_lines = [] # Reset article buffer
            
            current_part = line
            current_chapter = "" # Reset lower levels
            current_section = ""
            continue
            
        if p_chap.match(line):
            save_current_article()
            current_article_lines = []
            
            current_chapter = line
            current_section = "" # Reset lower levels
            continue
            
        if p_sec.match(line):
            save_current_article()
            current_article_lines = []
            
            current_section = line
            continue
            
        # Check Article Start
        is_article_start = False
        if p_art.match(line):
            # Validate false positive (như logic cũ)
            if current_article_lines:
                prev_text = current_article_lines[-1].strip().lower()
                last_word = prev_text.split()[-1] if prev_text else ""
                last_word = re.sub(r'[^\w]', '', last_word)
                if last_word not in invalid_prefixes:
                    is_article_start = True
            else:
                is_article_start = True
        
        if is_article_start:
            save_current_article() # Save old one
            current_article_lines = [line] # Start new one
        else:
            # Normal content line
            if current_article_lines: # Only add if we are inside an article
                current_article_lines.append(line)
    
    # End loop: Save last article
    save_current_article()
    
    # Filter sequence as before
    # Note: filter_chunks_by_sequence logic relies on raw text "Điều X", 
    # but now we have "[Thuộc ...] \n Điều X". 
    # We need to adapt the regex in filter or clean inputs before filtering.
    # The current `get_article_num` uses `^Điều \d+`, which will fail if context is prepended.
    
    # Let's fix filter_chunks_by_sequence to handle new format
    # Instead of modifying it here (expensive), I will address it in `get_article_num` update.
    return filter_chunks_by_sequence(final_chunks)


def filter_chunks_by_sequence(chunks):
    """
    Lọc các chunk theo thuật toán 'Lookahead GAP Check'
    Mục tiêu: Build chuỗi 1, 2, 3... 689.
    Xử lý:
    - Nếu gặp đúng next_num: Lấy.
    - Nếu gặp num > next_num (Gap): Check xem next_num có tồn tại ở phía sau không?
      + Có: num hiện tại là Tham chiếu (Forward Reference) -> Bỏ qua.
      + Không: Chấp nhận Gap (Có thể do lỗi PDF mất trang).
    """
    if not chunks: return []

    # Parse hết ra list dict để dễ xử lý
    parsed_chunks = []
    def get_article_num(c):
        # Regex updated to ignore "[Thuộc ...]\n" prefix
        # Search for "Điều X" anywhere in the start or after a newline
        m = re.search(r'(^|\n)Điều (\d+)', c, re.IGNORECASE)
        if not m: return -1, 0
        
        return int(m.group(2)), len(c)

    for c in chunks:
        num, length = get_article_num(c)
        if num > 0:
            parsed_chunks.append({"num": num, "content": c, "len": length})
            
    final_list = []
    current_num = 0
    
    # Tạo set các số tồn tại để lookup nhanh O(1)
    available_nums = {p["num"] for p in parsed_chunks}
    
    for item in parsed_chunks:
        num = item["num"]
        expected = current_num + 1
        
        # 1. Khớp hoàn hảo
        if num == expected:
            final_list.append(item["content"])
            current_num = num
            continue
            
        # 2. Tham chiếu ngược hoặc Duplicate (Reference to past)
        if num <= current_num:
            # print(f"-> Bỏ qua Điều {num} (Duplicate/BackRef)")
            continue
            
        # 3. Gap (Nhảy cóc): num > expected
        # Đây là case quyết định: Liệu num này là Next Real Article hay là Forward Reference?
        # Check: Liệu 'expected' (ví dụ 11) có tồn tại trong danh sách các số CÒN LẠI không?
        # Tuy nhiên available_nums chứa toàn bộ, ko biết vị trí.
        # Nhưng logic đơn giản: Nếu 'expected' nằm trong tập available_nums, thì khả năng cao
        # chúng ta chưa gặp nó, vậy cái 'num' to đùng này là Reference.
        
        # Cải tiến: Check range.
        # Nếu chúng ta đang ở 10, gặp 15. Mà trong list có 11, 12, 13...
        # Thì 15 này là rác.
        
        # Nhưng available_nums là global. Nếu "Điều 11" tồn tại nhưng nó LẠI là Reference ở đâu đó xa lắc?
        # Rủi ro thấp. Vì Reference thường ko ở đầu dòng chuẩn như Regex ^Điều \d+.
        
        if expected in available_nums:
            # OK, số mình đang tìm (expected) CÓ tồn tại trong tài liệu.
            # Vậy số 'num' hiện tại (lớn hơn expected) khả năng cao là Reference chen ngang.
            # ACTION: Bỏ qua 'num' này, kiên nhẫn đợi 'expected' xuất hiện.
            # print(f"-> Bỏ qua Điều {num} (ForwardRef - Đang chờ Điều {expected})")
            continue
        else:
            # Số mình đang tìm KHÔNG tồn tại trong cả tài liệu (có thể do lỗi OCR fail ko bắt dc).
            # Đành chấp nhận Gap. Lấy 'num' làm mốc mới.
            # Nhưng khoan, nếu gap quá lớn (VD từ 10 nhảy lên 600)?
            if num - current_num > 50:
                 # Gap quá lớn, khả năng là Reference tới Điều khoản thi hành cuối cùng.
                 # Check xem có số nào nhỏ hơn num mà > current_num không?
                 # VD: đang 10, gặp 600. Nhưng trong list còn có 15, 20...
                 # Logic: min(k for k in available_nums if k > current_num)
                 # Nếu min đó < num, thì num này là Reference xa.
                 upcoming = [k for k in available_nums if k > current_num]
                 if upcoming:
                     min_upcoming = min(upcoming)
                     if min_upcoming < num:
                         continue # Bỏ qua 600, để chờ 15.

            final_list.append(item["content"])
            current_num = num

    print(f"\n[Sequential Filter v2] Giữ lại {len(final_list)} chunk từ {len(chunks)} chunk ban đầu.")
    return final_list

def process_file(file_path):
    raw_text = read_pdf(file_path)
    print(f"Tổng số ký tự raw: {len(raw_text)}")
    
    if len(raw_text) == 0:
        print("CẢNH BÁO: File PDF chưa đọc được text. Vui lòng kiểm tra lại file.")
        return []

    cleaned_text = clean_text(raw_text)
    print(f"Tổng số ký tự sau khi clean: {len(cleaned_text)}")
    
    # In một đoạn text đã clean để check pattern
    print("\n[DEBUG - Preview Cleaned Text (500 chars)]:")
    print(cleaned_text[:500])
    print("-" * 50 + "\n")
    
    chunks = chunk_by_article(cleaned_text)
    print(f"Số lượng 'Điều' tìm thấy: {len(chunks)}")
    
    if chunks:
        print("\n[Preview Chunk Đầu Tiên (Điều 1?)]:")
        print(chunks[0][:300] + "...")
        print("\n[Preview Chunk Cuối Cùng (Điều 689?)]:")
        print(chunks[-1][:300] + "...")
    else:
        print("CẢNH BÁO: Không tìm thấy Điều luật nào. Kiểm tra lại Regex hoặc file PDF.")
    
    return chunks

if __name__ == "__main__":
    print("Bắt đầu xử lý...")
    process_file(FILE_PATH)
