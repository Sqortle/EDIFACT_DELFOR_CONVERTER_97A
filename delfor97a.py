import xml.etree.ElementTree as ET


class XMLConverter():

    def __init__(self, edifact_message):
        self.edifact_message = edifact_message
        self.segments_class = SegmentsClass(self)
        self.root = self.convert(edifact_message)

    def sanitize(self, text):
        if text is None:
            return ""
        return str(text).replace("\n", "").replace("\r", "").strip()

    def safe_split_component(self, component):
        try:
            return component.split(":")[0], component.split(":")[1]
        except IndexError:
            return component, ""

    def indent(self, elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for e in elem:
                self.indent(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def convert(self, edifact_message):
        segments = [line.strip() for line in edifact_message.split("'") if line.strip()]

        root = ET.Element("SCHEDULES")
        schedules_el = ET.SubElement(root, "SCHEDULES")
        schedule = ET.SubElement(schedules_el, "SCHEDULE")

        ET.SubElement(schedule, "SUPP_SCHED_TYPE").text = "DELFOR"

        for seg in segments:
            parts = seg.split("+")
            tag = parts[0]

            if tag == "NAD":
                self.segments_class.NADfunction(schedule, parts)
            elif tag == "BGM":
                self.segments_class.BGMfunction(schedule, parts)
            elif tag == "DTM":
                self.segments_class.DTMfunction(schedule, parts, "0", None, None)

        article_lines_el = ET.SubElement(schedule, "ARTICLE_LINES")
        demand_lines_el = ET.SubElement(schedule, "DEMAND_LINES")
        current_article_line = None
        schedule_no = 0
        line_type_id = "1"
        current_SCC_no = None
        current_demand_line = None
        is_scc_activate = 0

        for seg in segments:
            parts = seg.split("+")
            tag = parts[0]

            if tag == "LIN":
                schedule_no += 1
                schedule_no_str = str(schedule_no)
                current_article_line = self.segments_class.LINfunction(schedule, parts, article_lines_el,
                                                                       schedule_no_str)

            elif tag == "SCC":
                current_SCC_no = parts[1]
                if current_SCC_no == "4":
                    schedule_no_str = str(schedule_no)
                    current_demand_line = ET.SubElement(demand_lines_el, "SCHEDULE_LINE")
                    self.segments_class.SCCfunction(schedule, schedule_no_str, line_type_id, current_demand_line)
                    is_scc_activate = 1
                else:
                    is_scc_activate = 0
            elif tag == "QTY" and current_article_line is not None:
                self.segments_class.QTYfunction(parts, current_article_line, current_demand_line, is_scc_activate)
            elif tag == "DTM" and current_article_line is not None:
                self.segments_class.DTMfunction(schedule, parts, current_SCC_no, current_demand_line,
                                                current_article_line)
            elif tag == "RFF":
                self.segments_class.RFFfunction(current_article_line, parts)

        return root


class SegmentsClass():

    def __init__(self, converter):
        self.converter = converter

    def NADfunction(self, schedule, parts):
        party_qualifier = parts[1]
        party_id = self.converter.sanitize(parts[2].split(":")[0])
        if party_qualifier == "SU":
            ET.SubElement(schedule, "VENDOR_NO").text = party_id
        elif party_qualifier == "SF":
            ET.SubElement(schedule, "SHIP_FROM").text = party_id

    def BGMfunction(self, schedule, parts):
        ET.SubElement(schedule, "MESSAGE_ID").text = self.converter.sanitize(parts[2] if len(parts) > 2 else "")

    def DTMfunction(self, schedule, parts, current_SCC_no, current_demand_line, current_article_line):
        if len(parts) < 2:
            return
        split_parts = parts[1].split(":")
        date_qualifier = split_parts[0]
        date_value = split_parts[1] if len(split_parts) > 1 else ""
        formatted_date = f"{date_value[:2]}-{date_value[2:4]}-{date_value[4:]}T00:00:00" if date_value else ""

        if not formatted_date:
            return

        if date_qualifier == "158" and current_SCC_no == "4":
            ET.SubElement(current_demand_line, "DELIVERY_DUE_DATE").text = formatted_date
            ET.SubElement(current_demand_line, "TO_DATE").text = formatted_date
        elif date_qualifier == "137":
            ET.SubElement(schedule, "VALID_FROM").text = formatted_date
        elif date_qualifier == "11" and current_article_line is not None:
            ET.SubElement(current_article_line, "LAST_RECEIPT_DATE").text = formatted_date
        elif date_qualifier == "159":
            ET.SubElement(schedule, "VALID_UNTIL").text = formatted_date
        # elif date_qualifier == "51":

    def RFFfunction(self, current_article_line, parts):
        ref_parts = parts[1].split(":") if len(parts) > 1 else ["", ""]
        ET.SubElement(current_article_line, "SUPPLIER_REF").text = self.converter.sanitize(
            ref_parts[1] if len(ref_parts) > 1 else "")

    def QTYfunction(self, parts, current_article_line, current_demand_line, is_scc_activate):
        qty_val = "0"
        if len(parts) > 1 and ":" in parts[1]:
            qty_val = self.converter.sanitize(parts[1].split(":")[1])
        qty_parts = parts[1].split(":")

        if qty_parts[0] == "79":
            ET.SubElement(current_article_line, "LAST_RECEIPT_QTY").text = qty_val
        elif qty_parts[0] == "3" and is_scc_activate == 1:
            ET.SubElement(current_demand_line, "CUMULATIVE_QUANTITY_DUE").text = qty_parts[1]
        # elif qty_parts[0] == "12":

    def LINfunction(self, schedule, parts, article_lines_el, schedule_no_str):
        current_article_line = ET.SubElement(article_lines_el, "ARTICLE_LINE")
        ean_code = self.converter.sanitize(parts[3].split(":")[0]) if len(parts) > 3 and ":" in parts[3] else ""
        ET.SubElement(current_article_line, "EAN_CODE").text = ean_code
        ET.SubElement(current_article_line, "CALL_OFF_NO").text = self.converter.sanitize(
            schedule.findtext("MESSAGE_ID", ""))
        ET.SubElement(current_article_line, "SCHEDULE_NO").text = schedule_no_str
        return current_article_line

    def SCCfunction(self, schedule, schedule_no_str, line_type_id, current_demand_line):
        ET.SubElement(current_demand_line, "LINE_TYPE_ID").text = line_type_id
        ET.SubElement(current_demand_line, "DOCK_CODE").text = self.converter.sanitize(
            schedule.findtext("SHIP_FROM", ""))
        ET.SubElement(current_demand_line, "SCHEDULE_NO").text = schedule_no_str
        ET.SubElement(current_demand_line, "CUSTOMER_PO_NO").text = self.converter.sanitize(
            schedule.findtext("MESSAGE_ID", ""))
        return current_demand_line


edifact_message = """

"""

convert = XMLConverter(edifact_message)
convert.indent(convert.root)
tree = ET.ElementTree(convert.root)
tree.write("delforoutput.xml", encoding="ISO-8859-1", xml_declaration=True)


