"""
ETL script to ingest MMTPL Vendors, Purchase Orders, PO Items, and Client Invoices into SQLite & Supabase.
"""

import sys
import os
import csv
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
BASE_DIR = Path(__file__).resolve().parent / "backend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import Base
from app.models import (
    MaterialMaster, Contractor, InwardTransaction, ContractorTransaction, 
    TransactionAudit, User, VendorMaster, PurchaseOrder, PurchaseOrderItem, ClientInvoice
)
from app.migration.build_procurement_dataset import VENDORS

# Detailed Purchase Orders dataset
RAW_POS_DATA = [
    {
        "po_no": "MMTPL/PO/LMEL/25-26/001",
        "po_date": "2026-03-05",
        "vendor_code": "V001",
        "total_taxable": 373130.0,
        "sgst_amount": 33581.70,
        "cgst_amount": 33581.70,
        "igst_amount": 0.0,
        "gross_amount": 440293.40,
        "payment_terms": "50% advance & balance 30 days",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "ARC WELDING MACHINE 400 AMP (Industrial Weld)", "gst": 0.18, "uom": "NOS", "qty": 5, "price": 29000.0, "total": 145000.0, "type": "ASSET"},
            {"sl_no": 2, "desc": "MIG MACHINE 400 15M CABLE TORCH (Rillon)", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 82500.0, "total": 82500.0, "type": "ASSET"},
            {"sl_no": 3, "desc": "WIRE ROPE SLING 25MM X 6MTRS", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 4650.0, "total": 18600.0, "type": "ASSET"},
            {"sl_no": 4, "desc": "WIRE ROPE SLING 19MM X 6MTRS", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 2850.0, "total": 11400.0, "type": "ASSET"},
            {"sl_no": 5, "desc": "WIRE ROPE SLING 16MM X 6MTRS", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 2250.0, "total": 9000.0, "type": "ASSET"},
            {"sl_no": 6, "desc": "CHAIN PULLEY BLOCK 3T 6M", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 11930.0, "total": 11930.0, "type": "ASSET"},
            {"sl_no": 7, "desc": "CHAIN PULLEY BLOCK 2T 6M", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 9600.0, "total": 9600.0, "type": "ASSET"},
            {"sl_no": 8, "desc": "MOTHER OVEN HMP", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 26500.0, "total": 26500.0, "type": "ASSET"},
            {"sl_no": 9, "desc": "ELECTRICAL PANEL WITH BOARDS", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 23500.0, "total": 23500.0, "type": "ASSET"},
            {"sl_no": 10, "desc": "SAFETY BELT FULL BODY HARNESS", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 1650.0, "total": 16500.0, "type": "ASSET"},
            {"sl_no": 11, "desc": "WIRE ROPE 10MM", "gst": 0.18, "uom": "MTRS", "qty": 100, "price": 110.0, "total": 11000.0, "type": "ASSET"},
            {"sl_no": 12, "desc": "WIRE ROPE CLAMP 10MM", "gst": 0.18, "uom": "NOS", "qty": 20, "price": 40.0, "total": 800.0, "type": "ASSET"},
            {"sl_no": 13, "desc": "CHAIN LINK 6 TON CAPACITY", "gst": 0.18, "uom": "NOS", "qty": 8, "price": 850.0, "total": 6800.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/25-26/001-B",
        "po_date": "2026-03-18",
        "vendor_code": "V008",
        "total_taxable": 35600.0,
        "sgst_amount": 0.0,
        "cgst_amount": 0.0,
        "igst_amount": 6408.0,
        "gross_amount": 42008.0,
        "payment_terms": "100% Advance before Dispatch",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "Brick Cutting Blade 16\" Diamond Segmented", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 3500.0, "total": 35000.0, "type": "CONSUMABLE"},
            {"sl_no": 2, "desc": "Transportation - VRL Logistic", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 600.0, "total": 600.0, "type": "SERVICE"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/25-26/002",
        "po_date": "2026-03-18",
        "vendor_code": "V002",
        "total_taxable": 390670.0,
        "sgst_amount": 35160.30,
        "cgst_amount": 35160.30,
        "igst_amount": 0.0,
        "gross_amount": 460990.60,
        "payment_terms": "50% advance & balance 30 days",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "CHAIN PULLEY BLOCK 3T 6M Safelift", "gst": 0.18, "uom": "NOS", "qty": 3, "price": 19500.0, "total": 58500.0, "type": "ASSET"},
            {"sl_no": 2, "desc": "CHAIN PULLEY BLOCK 2T 6M Safelift", "gst": 0.18, "uom": "NOS", "qty": 3, "price": 16710.0, "total": 50130.0, "type": "ASSET"},
            {"sl_no": 3, "desc": "MOTHER OVEN HMP ISI", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 25500.0, "total": 25500.0, "type": "ASSET"},
            {"sl_no": 4, "desc": "ELECTRICAL PANEL WITH BOARDS", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 4700.0, "total": 9400.0, "type": "ASSET"},
            {"sl_no": 5, "desc": "SAFETY BELT FULL BODY HARNESS", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 1700.0, "total": 17000.0, "type": "ASSET"},
            {"sl_no": 6, "desc": "WIRE ROPE 10MM", "gst": 0.18, "uom": "MTRS", "qty": 100, "price": 88.0, "total": 8800.0, "type": "ASSET"},
            {"sl_no": 7, "desc": "WIRE ROPE CLAMP 10MM", "gst": 0.18, "uom": "NOS", "qty": 20, "price": 35.0, "total": 700.0, "type": "ASSET"},
            {"sl_no": 8, "desc": "NUMBER PUNCH SET 1/2\"", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 6500.0, "total": 6500.0, "type": "ASSET"},
            {"sl_no": 9, "desc": "LETTER PUNCH SET 1/2\"", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 2310.0, "total": 2310.0, "type": "ASSET"},
            {"sl_no": 10, "desc": "POWER CABLE 1.5 Sq. mm / 2 core", "gst": 0.18, "uom": "ROLL", "qty": 1, "price": 3100.0, "total": 3100.0, "type": "ASSET"},
            {"sl_no": 11, "desc": "POWER CABLE 2.5 Sq. mm / 3 core", "gst": 0.18, "uom": "ROLL", "qty": 2, "price": 6500.0, "total": 13000.0, "type": "ASSET"},
            {"sl_no": 12, "desc": "POWER CABLE 4.0 Sq. mm / 4 core", "gst": 0.18, "uom": "ROLL", "qty": 2, "price": 12000.0, "total": 24000.0, "type": "ASSET"},
            {"sl_no": 13, "desc": "INSULATION TAPE", "gst": 0.18, "uom": "NOS", "qty": 20, "price": 10.0, "total": 200.0, "type": "CONSUMABLE"},
            {"sl_no": 14, "desc": "32A MALE/FEMALE SOCKET", "gst": 0.18, "uom": "SET", "qty": 10, "price": 360.0, "total": 3600.0, "type": "ASSET"},
            {"sl_no": 15, "desc": "16A MALE/FEMALE SOCKET", "gst": 0.18, "uom": "SET", "qty": 10, "price": 200.0, "total": 2000.0, "type": "ASSET"},
            {"sl_no": 16, "desc": "100W LED HALOGEN FLOOD LIGHT", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 1800.0, "total": 18000.0, "type": "ASSET"},
            {"sl_no": 17, "desc": "WELDING ELECTRODES 6013 4.0MM D&H", "gst": 0.18, "uom": "CASES", "qty": 15, "price": 2200.0, "total": 33000.0, "type": "CONSUMABLE"},
            {"sl_no": 18, "desc": "HAND GLOVES COTTON", "gst": 0.18, "uom": "PAIR", "qty": 50, "price": 15.0, "total": 750.0, "type": "CONSUMABLE"},
            {"sl_no": 19, "desc": "HAND GLOVES LEATHER", "gst": 0.18, "uom": "PAIR", "qty": 25, "price": 260.0, "total": 6500.0, "type": "CONSUMABLE"},
            {"sl_no": 20, "desc": "LINE DORI", "gst": 0.18, "uom": "BDL", "qty": 20, "price": 10.0, "total": 200.0, "type": "CONSUMABLE"},
            {"sl_no": 21, "desc": "TEFLON TAPE", "gst": 0.18, "uom": "NOS", "qty": 20, "price": 10.0, "total": 200.0, "type": "CONSUMABLE"},
            {"sl_no": 22, "desc": "SILICON SPRAY FOR MIG", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 260.0, "total": 2600.0, "type": "CONSUMABLE"},
            {"sl_no": 23, "desc": "WELDING HOLDER HEAVY DUTY", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 260.0, "total": 2600.0, "type": "ASSET"},
            {"sl_no": 24, "desc": "DA REGULATOR HMP ISI", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 3200.0, "total": 32000.0, "type": "ASSET"},
            {"sl_no": 25, "desc": "CUTTING NOZZLE (DA) 1/16", "gst": 0.18, "uom": "NOS", "qty": 20, "price": 400.0, "total": 8000.0, "type": "CONSUMABLE"},
            {"sl_no": 26, "desc": "CUTTING NOZZLE (DA) 3/64", "gst": 0.18, "uom": "NOS", "qty": 20, "price": 400.0, "total": 8000.0, "type": "CONSUMABLE"},
            {"sl_no": 27, "desc": "WIRE ROPE SLING 25MM X 6M", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 5135.0, "total": 20540.0, "type": "ASSET"},
            {"sl_no": 28, "desc": "WIRE ROPE SLING 19MM X 6M", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 3835.0, "total": 15340.0, "type": "ASSET"},
            {"sl_no": 29, "desc": "WIRE ROPE SLING 16MM X 6M", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 2405.0, "total": 9620.0, "type": "ASSET"},
            {"sl_no": 30, "desc": "WIRE ROPE SLING 16MM X 4M", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 2145.0, "total": 8580.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/25-26/003",
        "po_date": "2026-03-19",
        "vendor_code": "V002",
        "total_taxable": 187110.0,
        "sgst_amount": 16839.90,
        "cgst_amount": 16839.90,
        "igst_amount": 0.0,
        "gross_amount": 220789.80,
        "payment_terms": "50% advance & balance 30 days",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "Bending Wire", "gst": 0.18, "uom": "KGS", "qty": 10, "price": 75.0, "total": 750.0, "type": "CONSUMABLE"},
            {"sl_no": 2, "desc": "Measuring Tape 5 Mtrs", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 90.0, "total": 900.0, "type": "ASSET"},
            {"sl_no": 3, "desc": "Measuring Tape 50 Mtrs", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 850.0, "total": 1700.0, "type": "ASSET"},
            {"sl_no": 4, "desc": "Spirit Level 24\"", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 650.0, "total": 6500.0, "type": "ASSET"},
            {"sl_no": 5, "desc": "Aluminum Paata 6\"", "gst": 0.18, "uom": "NOS", "qty": 24, "price": 850.0, "total": 20400.0, "type": "ASSET"},
            {"sl_no": 6, "desc": "GI Buckets 10L Heavy", "gst": 0.18, "uom": "NOS", "qty": 50, "price": 350.0, "total": 17500.0, "type": "ASSET"},
            {"sl_no": 7, "desc": "Coconut Brush", "gst": 0.18, "uom": "NOS", "qty": 100, "price": 100.0, "total": 10000.0, "type": "CONSUMABLE"},
            {"sl_no": 8, "desc": "Nails 1.5 inch", "gst": 0.18, "uom": "KGS", "qty": 150, "price": 75.0, "total": 11250.0, "type": "CONSUMABLE"},
            {"sl_no": 9, "desc": "Line Dori", "gst": 0.18, "uom": "ROLL", "qty": 50, "price": 10.0, "total": 500.0, "type": "CONSUMABLE"},
            {"sl_no": 10, "desc": "Hand Mortar Mixer", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 3900.0, "total": 7800.0, "type": "ASSET"},
            {"sl_no": 11, "desc": "Air Blower", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 2650.0, "total": 5300.0, "type": "ASSET"},
            {"sl_no": 12, "desc": "Safety Belt", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 1700.0, "total": 17000.0, "type": "CONSUMABLE"},
            {"sl_no": 13, "desc": "21-23 Ring Spanners", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 160.0, "total": 1600.0, "type": "ASSET"},
            {"sl_no": 14, "desc": "Pipe Cutting Machine Ken Polymak", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 9400.0, "total": 9400.0, "type": "ASSET"},
            {"sl_no": 15, "desc": "14 inch Cutting Blade Double Net", "gst": 0.18, "uom": "NOS", "qty": 25, "price": 125.0, "total": 3125.0, "type": "CONSUMABLE"},
            {"sl_no": 16, "desc": "Hand Gloves Gray", "gst": 0.18, "uom": "PAIR", "qty": 1000, "price": 25.0, "total": 25000.0, "type": "CONSUMABLE"},
            {"sl_no": 17, "desc": "Dust Mask", "gst": 0.18, "uom": "NOS", "qty": 500, "price": 10.0, "total": 5000.0, "type": "CONSUMABLE"},
            {"sl_no": 18, "desc": "Web Sling 3T 5M", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 650.0, "total": 2600.0, "type": "ASSET"},
            {"sl_no": 19, "desc": "Web Sling 3T 6M", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 750.0, "total": 3000.0, "type": "ASSET"},
            {"sl_no": 20, "desc": "Wire Rope Sling 2T X 2M", "gst": 0.18, "uom": "NOS", "qty": 8, "price": 1600.0, "total": 12800.0, "type": "ASSET"},
            {"sl_no": 21, "desc": "1 HP Water Motor", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 4800.0, "total": 4800.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/027",
        "po_date": "2026-06-17",
        "vendor_code": "V005",
        "total_taxable": 20640000.0,
        "sgst_amount": 0.0,
        "cgst_amount": 0.0,
        "igst_amount": 3715200.0,
        "gross_amount": 24598752.0,
        "payment_terms": "Advance against PO & Balance to be paid through Finance",
        "delivery_terms": "2-3 weeks, free delivery at door",
        "notes": "Discount of Rs. 3,40,000 provided per machine on 6 machines (Total discount Rs. 20,40,000). Includes 2 Man Baskets and Spare Kits worth Rs. 25,000 free.",
        "items": [
            {"sl_no": 1, "desc": "ACE Hydraulic Mobile Crane F170 (17 Ton Cap / BS V 4X4 TATA 74HP Engine)", "gst": 0.18, "uom": "NOS", "qty": 6, "price": 3440000.0, "total": 20640000.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/028",
        "po_date": "2026-06-17",
        "vendor_code": "V005",
        "total_taxable": 5600000.0,
        "sgst_amount": 0.0,
        "cgst_amount": 0.0,
        "igst_amount": 1008000.0,
        "gross_amount": 6674080.0,
        "payment_terms": "Advance against PO & Balance to be paid through Finance",
        "delivery_terms": "2-3 weeks, free delivery at door",
        "notes": "Discount of Rs. 5,00,000 provided on basic value. Includes 1 Spare Kit worth Rs. 25,000 free.",
        "items": [
            {"sl_no": 1, "desc": "ACE Hydraulic Mobile Crane NX 360 (20 Ton Cap / BS V 4X4 TATA 101HP Engine)", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 5600000.0, "total": 5600000.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/021",
        "po_date": "2026-05-20",
        "vendor_code": "V001",
        "total_taxable": 1180290.0,
        "sgst_amount": 106226.10,
        "cgst_amount": 106226.10,
        "igst_amount": 0.0,
        "gross_amount": 1392742.20,
        "payment_terms": "50% advance & balance 30 days",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "WELDING CABLE 95 SQMM", "gst": 0.18, "uom": "MTRS", "qty": 300, "price": 140.0, "total": 42000.0, "type": "ASSET"},
            {"sl_no": 2, "desc": "WELDING HELMET", "gst": 0.18, "uom": "NOS", "qty": 20, "price": 250.0, "total": 5000.0, "type": "ASSET"},
            {"sl_no": 3, "desc": "WELDING HOLDER Heavy Duty", "gst": 0.18, "uom": "NOS", "qty": 20, "price": 320.0, "total": 6400.0, "type": "ASSET"},
            {"sl_no": 4, "desc": "CUTTING TORCH 3 Pipes", "gst": 0.18, "uom": "NOS", "qty": 6, "price": 3650.0, "total": 21900.0, "type": "ASSET"},
            {"sl_no": 5, "desc": "OXYGEN REGULATOR Double Gauge", "gst": 0.18, "uom": "NOS", "qty": 15, "price": 2650.0, "total": 39750.0, "type": "ASSET"},
            {"sl_no": 6, "desc": "DA REGULATOR", "gst": 0.18, "uom": "NOS", "qty": 15, "price": 2950.0, "total": 44250.0, "type": "ASSET"},
            {"sl_no": 7, "desc": "PUG MACHINE Konark", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 14500.0, "total": 29000.0, "type": "ASSET"},
            {"sl_no": 8, "desc": "PUG MACHINE TRACK", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 1350.0, "total": 5400.0, "type": "ASSET"},
            {"sl_no": 9, "desc": "A7 GRINDING MACHINE 2600W Bosch", "gst": 0.18, "uom": "NOS", "qty": 8, "price": 9200.0, "total": 73600.0, "type": "ASSET"},
            {"sl_no": 10, "desc": "A5 GRINDING MACHINE 1300W Bosch", "gst": 0.18, "uom": "NOS", "qty": 8, "price": 6500.0, "total": 52000.0, "type": "ASSET"},
            {"sl_no": 11, "desc": "HYDRAULIC JACK 50 TON CAPACITY", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 24500.0, "total": 49000.0, "type": "ASSET"},
            {"sl_no": 12, "desc": "CHAIN PULLEY BLOCK 10T X 6M", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 35200.0, "total": 70400.0, "type": "ASSET"},
            {"sl_no": 13, "desc": "CHAIN PULLEY BLOCK 5T X 6M", "gst": 0.18, "uom": "NOS", "qty": 10, "price": 16350.0, "total": 163500.0, "type": "ASSET"},
            {"sl_no": 14, "desc": "CHAIN PULLEY BLOCK 3T X 6M", "gst": 0.18, "uom": "NOS", "qty": 6, "price": 12850.0, "total": 77100.0, "type": "ASSET"},
            {"sl_no": 15, "desc": "ELECTRICAL PANEL BOARD", "gst": 0.18, "uom": "NOS", "qty": 8, "price": 19500.0, "total": 156000.0, "type": "ASSET"},
            {"sl_no": 16, "desc": "BAKING OVEN HEAVY DUTY", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 27500.0, "total": 27500.0, "type": "ASSET"},
            {"sl_no": 17, "desc": "PORTABLE OVEN", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 2250.0, "total": 9000.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/056",
        "po_date": "2026-11-24",
        "vendor_code": "V003",
        "total_taxable": 843030.0,
        "sgst_amount": 0.0,
        "cgst_amount": 0.0,
        "igst_amount": 137900.40,
        "gross_amount": 980930.40,
        "payment_terms": "Immediate on Delivery",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "WELDING ELECTRODE 6013 3.15MM X 450MM", "gst": 0.18, "uom": "CASE", "qty": 50, "price": 1950.0, "total": 97500.0, "type": "CONSUMABLE"},
            {"sl_no": 2, "desc": "WELDING ELECTRODE 6013 4.0MM X 450MM", "gst": 0.18, "uom": "CASE", "qty": 40, "price": 2010.0, "total": 80400.0, "type": "CONSUMABLE"},
            {"sl_no": 3, "desc": "WELDING ELECTRODE 7018 3.15MM X 450MM", "gst": 0.18, "uom": "CASE", "qty": 80, "price": 1940.0, "total": 155200.0, "type": "CONSUMABLE"},
            {"sl_no": 4, "desc": "WELDING ELECTRODE 7018 4.0MM X 450MM", "gst": 0.18, "uom": "CASE", "qty": 50, "price": 2010.0, "total": 100500.0, "type": "CONSUMABLE"},
            {"sl_no": 5, "desc": "MIG COIL D&H", "gst": 0.18, "uom": "ROLL", "qty": 150, "price": 115.0, "total": 17250.0, "type": "CONSUMABLE"},
            {"sl_no": 6, "desc": "CUTTING WHEEL AG7", "gst": 0.18, "uom": "NOS", "qty": 100, "price": 80.0, "total": 8000.0, "type": "CONSUMABLE"},
            {"sl_no": 7, "desc": "GRINDING WHEEL AG7", "gst": 0.18, "uom": "NOS", "qty": 200, "price": 85.0, "total": 17000.0, "type": "CONSUMABLE"},
            {"sl_no": 8, "desc": "GRINDING WHEEL AG5", "gst": 0.18, "uom": "NOS", "qty": 150, "price": 60.0, "total": 9000.0, "type": "CONSUMABLE"},
            {"sl_no": 9, "desc": "SAFETY SHOES FOR LABOUR SIZE 7-9", "gst": 0.05, "uom": "PAIR", "qty": 240, "price": 330.0, "total": 79200.0, "type": "CONSUMABLE"},
            {"sl_no": 10, "desc": "COTTON HAND GLOVES", "gst": 0.05, "uom": "PAIR", "qty": 500, "price": 15.0, "total": 7500.0, "type": "CONSUMABLE"},
            {"sl_no": 11, "desc": "SAFETY HELMET YELLOW", "gst": 0.18, "uom": "NOS", "qty": 100, "price": 105.0, "total": 10500.0, "type": "CONSUMABLE"},
            {"sl_no": 12, "desc": "WELDING CABLE 95 SQMM", "gst": 0.18, "uom": "MTRS", "qty": 500, "price": 90.0, "total": 45000.0, "type": "ASSET"},
            {"sl_no": 13, "desc": "WELDING HOLDER 1000A", "gst": 0.18, "uom": "NOS", "qty": 50, "price": 260.0, "total": 13000.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/024",
        "po_date": "2026-06-03",
        "vendor_code": "V007",
        "total_taxable": 726600.0,
        "sgst_amount": 0.0,
        "cgst_amount": 0.0,
        "igst_amount": 130788.0,
        "gross_amount": 857388.0,
        "payment_terms": "100% on Delivery",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "SCAFFOLDING PIPES 48 OD (20 Kgs)", "gst": 0.18, "uom": "KGS", "qty": 8000, "price": 55.0, "total": 440000.0, "type": "ASSET"},
            {"sl_no": 2, "desc": "DROP FORGED CLAMP (FIXED)", "gst": 0.18, "uom": "NOS", "qty": 2000, "price": 103.0, "total": 206000.0, "type": "ASSET"},
            {"sl_no": 3, "desc": "SWIVEL CLAMP (MOVABLE)", "gst": 0.18, "uom": "NOS", "qty": 200, "price": 112.0, "total": 22400.0, "type": "ASSET"},
            {"sl_no": 4, "desc": "SLEEVE COUPLER (JOINTER)", "gst": 0.18, "uom": "NOS", "qty": 500, "price": 110.0, "total": 55000.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/025",
        "po_date": "2026-06-09",
        "vendor_code": "V015",
        "total_taxable": 254000.0,
        "sgst_amount": 22860.0,
        "cgst_amount": 22860.0,
        "igst_amount": 0.0,
        "gross_amount": 299720.0,
        "payment_terms": "Advance 50% on 20th June and balance within 15 days",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "VIRGO PLUS INVERTER W/M ARC-400 HDIJ (3PH)", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 28000.0, "total": 56000.0, "type": "ASSET"},
            {"sl_no": 2, "desc": "VIRGO MIG W/M 500-HDIJ WITH FEEDER UNIT (10M CABLE)", "gst": 0.18, "uom": "NOS", "qty": 2, "price": 99000.0, "total": 198000.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/030",
        "po_date": "2026-06-25",
        "vendor_code": "V007",
        "total_taxable": 126940.0,
        "sgst_amount": 0.0,
        "cgst_amount": 0.0,
        "igst_amount": 22849.20,
        "gross_amount": 149789.20,
        "payment_terms": "30-45 Days against Delivery",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "DIAL INDICATOR 0-10MM 2046A MITUTOYO", "gst": 0.18, "uom": "NOS", "qty": 8, "price": 3432.0, "total": 27456.0, "type": "ASSET"},
            {"sl_no": 2, "desc": "MAGNETIC DIAL STAND MITUTOYO 7010S", "gst": 0.18, "uom": "NOS", "qty": 8, "price": 2700.0, "total": 21600.0, "type": "ASSET"},
            {"sl_no": 3, "desc": "MICROMETER 0-150 OUTSIDE MITUTOYO", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 20016.0, "total": 20016.0, "type": "ASSET"},
            {"sl_no": 4, "desc": "OUTSIDE MICROMETER 150-300 MITUTOYO", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 29952.0, "total": 29952.0, "type": "ASSET"},
            {"sl_no": 5, "desc": "INSIDE MICROMETER 50-500 MITUTOYO", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 16416.0, "total": 16416.0, "type": "ASSET"},
            {"sl_no": 6, "desc": "MITUTOYO DIAL VERNIER CALIPER 0-300MM", "gst": 0.18, "uom": "NOS", "qty": 1, "price": 11500.0, "total": 11500.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/039",
        "po_date": "2026-09-23",
        "vendor_code": "V012",
        "total_taxable": 86000.0,
        "sgst_amount": 0.0,
        "cgst_amount": 0.0,
        "igst_amount": 15480.0,
        "gross_amount": 101480.0,
        "payment_terms": "100% Advance",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "TVS Forklift Tyres 6.50-10", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 8500.0, "total": 34000.0, "type": "ASSET"},
            {"sl_no": 2, "desc": "TVS Forklift Tyres 28.9-15", "gst": 0.18, "uom": "NOS", "qty": 4, "price": 13000.0, "total": 52000.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/040",
        "po_date": "2026-09-28",
        "vendor_code": "V011",
        "total_taxable": 74000.0,
        "sgst_amount": 6660.0,
        "cgst_amount": 6660.0,
        "igst_amount": 0.0,
        "gross_amount": 87320.0,
        "payment_terms": "100% Payment",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "Hydraulic Jack 50 Ton Capacity (RMT 100)", "gst": 0.18, "uom": "SET", "qty": 4, "price": 18500.0, "total": 74000.0, "type": "ASSET"}
        ]
    },
    {
        "po_no": "MMTPL/PO/LMEL/26-27/046",
        "po_date": "2026-10-07",
        "vendor_code": "V014",
        "total_taxable": 16500.0,
        "sgst_amount": 900.0,
        "cgst_amount": 900.0,
        "igst_amount": 0.0,
        "gross_amount": 18300.0,
        "payment_terms": "Immediate",
        "delivery_terms": "Immediate",
        "items": [
            {"sl_no": 1, "desc": "DUST MASK N4", "gst": 0.18, "uom": "NOS", "qty": 500, "price": 15.0, "total": 7500.0, "type": "CONSUMABLE"},
            {"sl_no": 2, "desc": "COTTON HAND GLOVES", "gst": 0.05, "uom": "PAIR", "qty": 500, "price": 18.0, "total": 9000.0, "type": "CONSUMABLE"}
        ]
    }
]

def load_client_invoices():
    csv_path = Path("data/client_billing_abstract.csv")
    if not csv_path.exists():
        return []
    
    invoices = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = None
        for row in reader:
            if not row or not any(row):
                continue
            if "SL No" in row and "Description" in row and not header:
                header = row
                continue
            if header and len(row) >= 16:
                if row[0] == "Gross Total" or "Gross Total" in row[1]:
                    break
                sl = None
                try: sl = int(row[0])
                except: pass
                
                desc = row[1].strip()
                bill_no = row[2].strip() if len(row) > 2 else ""
                loc = row[3].strip() if len(row) > 3 else "Ghugus, Chandrapur, MH"
                dept = row[4].strip() if len(row) > 4 else ""
                wo = row[5].strip() if len(row) > 5 else ""
                site = row[6].strip() if len(row) > 6 else "LMEL"
                bill_month = row[7].strip() if len(row) > 7 else ""
                inv_no = row[8].strip() if len(row) > 8 else ""
                
                if not inv_no:
                    continue
                
                b_date = None
                if len(row) > 9 and row[9].strip():
                    try:
                        b_date = datetime.strptime(row[9].strip(), "%Y-%m-%d")
                    except:
                        pass
                
                def parse_flt(val):
                    try:
                        clean = val.replace(",", "").strip()
                        return float(clean) if clean else 0.0
                    except:
                        return 0.0
                
                bill_amt = parse_flt(row[10])
                sgst = parse_flt(row[11]) if len(row) > 11 else 0.0
                cgst = parse_flt(row[12]) if len(row) > 12 else 0.0
                gross = parse_flt(row[13]) if len(row) > 13 else 0.0
                tds = parse_flt(row[14]) if len(row) > 14 else 0.0
                gross_tot = parse_flt(row[15]) if len(row) > 15 else 0.0
                rcvd = parse_flt(row[16]) if len(row) > 16 else 0.0
                bal = parse_flt(row[17]) if len(row) > 17 else 0.0

                invoices.append({
                    "invoice_no": inv_no,
                    "sl_no": sl,
                    "description": desc,
                    "bill_no": bill_no,
                    "location": loc,
                    "department": dept,
                    "work_order_no": wo,
                    "site": site,
                    "bill_month": bill_month,
                    "bill_date": b_date,
                    "bill_amount": bill_amt,
                    "sgst_amount": sgst,
                    "cgst_amount": cgst,
                    "gross_amount": gross,
                    "tds_amount": tds,
                    "gross_total_amount": gross_tot,
                    "received_amount": rcvd,
                    "balance_amount": bal,
                    "status": "Received" if rcvd > 0 and bal == 0 else "Billed"
                })
    return invoices

def run_ingestion(db_url: str):
    print(f"Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url}...", flush=True)
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("🔨 Ensuring all tables exist...", flush=True)
    Base.metadata.create_all(bind=engine)

    # Ensure added columns exist in materials table
    from sqlalchemy import text
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            res = conn.execute(text("PRAGMA table_info(materials)"))
            cols = [r[1] for r in res.fetchall()]
            if "standard_unit_price" not in cols:
                conn.execute(text("ALTER TABLE materials ADD COLUMN standard_unit_price FLOAT DEFAULT 0.0"))
            if "category_type" not in cols:
                conn.execute(text("ALTER TABLE materials ADD COLUMN category_type VARCHAR(50) DEFAULT 'Consumable'"))
            conn.commit()
        else:
            conn.execute(text("ALTER TABLE materials ADD COLUMN IF NOT EXISTS standard_unit_price FLOAT DEFAULT 0.0;"))
            conn.execute(text("ALTER TABLE materials ADD COLUMN IF NOT EXISTS category_type VARCHAR(50) DEFAULT 'Consumable';"))
            conn.commit()

    # 1. Ingest Vendors
    print(f"🏢 Syncing {len(VENDORS)} Vendors...", flush=True)
    for v in VENDORS:
        existing = session.query(VendorMaster).filter(VendorMaster.vendor_code == v["vendor_code"]).first()
        if not existing:
            session.add(VendorMaster(**v))
        else:
            for k, val in v.items():
                setattr(existing, k, val)
    session.commit()
    print("   ✓ Vendors synced.")

    # 2. Ingest Purchase Orders
    print(f"📄 Syncing {len(RAW_POS_DATA)} Purchase Orders with line items...", flush=True)
    for po in RAW_POS_DATA:
        items_data = po.pop("items", [])
        existing_po = session.query(PurchaseOrder).filter(PurchaseOrder.po_no == po["po_no"]).first()
        if not existing_po:
            po_date = datetime.strptime(po["po_date"], "%Y-%m-%d")
            new_po = PurchaseOrder(
                po_no=po["po_no"],
                po_date=po_date,
                vendor_code=po["vendor_code"],
                total_taxable=po["total_taxable"],
                sgst_amount=po["sgst_amount"],
                cgst_amount=po["cgst_amount"],
                igst_amount=po["igst_amount"],
                gross_amount=po["gross_amount"],
                payment_terms=po.get("payment_terms"),
                delivery_terms=po.get("delivery_terms"),
                notes=po.get("notes"),
                status="Approved"
            )
            session.add(new_po)
            session.flush()

            for item in items_data:
                session.add(PurchaseOrderItem(
                    po_no=po["po_no"],
                    sl_no=item["sl_no"],
                    item_description=item["desc"],
                    gst_rate=item.get("gst", 0.18),
                    uom=item.get("uom", "NOS"),
                    qty=item["qty"],
                    unit_price=item["price"],
                    taxable_value=item["total"],
                    remarks=item.get("type", "CONSUMABLE")
                ))
    session.commit()
    print("   ✓ Purchase Orders & Items synced.")

    # 3. Ingest Client Invoices (LMEL Ghugus)
    invoices = load_client_invoices()
    print(f"💰 Syncing {len(invoices)} Client Invoices (LMEL Billing Abstract)...", flush=True)
    for inv in invoices:
        existing_inv = session.query(ClientInvoice).filter(ClientInvoice.invoice_no == inv["invoice_no"]).first()
        if not existing_inv:
            session.add(ClientInvoice(**inv))
        else:
            for k, val in inv.items():
                setattr(existing_inv, k, val)
    session.commit()
    print("   ✓ Client Invoices synced.")

    # 4. Map Unit Purchase Prices to Materials
    print("💎 Mapping Unit Purchase Prices to Materials for Live Valuation...", flush=True)
    price_map = {
        "WELDING ELECTRODE 6013": 2010.0,
        "WELDING ELECTRODE 7018": 1940.0,
        "MIG WIRE": 120.0,
        "CUTTING WHEEL": 80.0,
        "GRINDING WHEEL": 85.0,
        "SAFETY SHOES": 350.0,
        "SAFETY HELMET": 150.0,
        "HAND GLOVES": 25.0,
        "WELDING CABLE": 120.0,
        "WELDING HOLDER": 260.0,
        "CUTTING TORCH": 3650.0,
        "OXYGEN REGULATOR": 2650.0,
        "DA REGULATOR": 2950.0,
        "CHAIN PULLEY BLOCK": 16350.0,
        "WIRE ROPE SLING": 3500.0,
        "FORGED CLAMP": 103.0,
        "SCAFFOLDING PIPE": 55.0,
        "BRICK CUTTING BLADE": 3500.0,
        "SAFETY BELT": 1700.0
    }

    materials = session.query(MaterialMaster).all()
    updated_count = 0
    for m in materials:
        m_name = (m.name or "").upper()
        for kw, pr in price_map.items():
            if kw in m_name:
                m.standard_unit_price = pr
                if any(akw in m_name for akw in ["MACHINE", "PULLEY", "CRANE", "OVEN", "JACK", "TORCH", "REGULATOR", "PANEL"]):
                    m.category_type = "Asset"
                else:
                    m.category_type = "Consumable"
                updated_count += 1
                break
    session.commit()
    print(f"   ✓ {updated_count} materials updated with real market purchasing prices.")

    # Compute Total Valuation
    from app.routers.dashboard import get_dashboard_stats
    stats = get_dashboard_stats(session)
    val = sum((m.standard_unit_price or 0.0) * max(0.0, (m.opening_stock or 0.0)) for m in materials)

    print("\n🎉 =============================================================")
    print("✅ PROCUREMENT & CLIENT BILLING INGESTION COMPLETE!")
    print(f"   • Total Active Vendors:         {session.query(VendorMaster).count()}")
    print(f"   • Purchase Orders Recorded:     {session.query(PurchaseOrder).count()}")
    print(f"   • PO Line Items:                {session.query(PurchaseOrderItem).count()}")
    print(f"   • Client Invoices (LMEL):       {session.query(ClientInvoice).count()}")
    print(f"   • Price-Mapped Materials:       {updated_count}")
    print("=============================================================\n", flush=True)

    session.close()

if __name__ == "__main__":
    # Ingest into local SQLite
    db_target = "sqlite:///mmtpl_store.db"
    run_ingestion(db_target)

    # Ingest into backend/mmtpl_store.db
    backend_db = "sqlite:///backend/mmtpl_store.db"
    if Path("backend/mmtpl_store.db").exists():
        run_ingestion(backend_db)

    # Ingest into cloud Supabase PostgreSQL
    supabase_url = "postgresql://postgres.bwmfahjmiodoalyadwni:Anantsoni2005@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require"
    try:
        print("☁️ Syncing procurement and billing to Supabase PostgreSQL...", flush=True)
        run_ingestion(supabase_url)
    except Exception as e:
        print(f"Warning: Cloud sync skipped or failed: {e}", flush=True)
