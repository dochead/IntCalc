import math
import uuid

from decimal import Decimal

class Loan(object):

    def __init__(self, principal, initial_rate, months = 240, initial_repayment = None, initial_fees = None, auto_adjust = False):
        self.principal = principal
        self.months = months
        self.auto_adjust = auto_adjust

        self.fee_structure = [{'id': unicode(uuid.uuid4().hex), 'month': 0, 'rate': initial_fees}]
        self.rate_structure = [{'id': unicode(uuid.uuid4().hex), 'month': 0, 'rate': initial_rate}]
        if not initial_repayment:
            initial_repayment = self.generate_repayment(self.principal, self.rate_structure[0]['rate'], self.months)
        self.repayment_structure = [{'id': unicode(uuid.uuid4().hex), 'month': 0, 'payment': initial_repayment, 'once_off': False}]
    
    def add_new_repayment(self, month, amount, once_off = True):
        new_payment = {'id': unicode(uuid.uuid4().hex), 'month': month, 'payment': amount, 'once_off': once_off}
        self.repayment_structure.append(new_payment)
        return {'id': new_payment['id']}
        
    def delete_repayment(self, id):
        self.repayment_structure = filter(lambda repayment: repayment['id'] != id, self.repayment_structure)
        return True
        
    def add_new_rate(self, month, rate):
        new_rate = {'id': unicode(uuid.uuid4().hex), 'month': month, 'rate': rate}
        self.rate_structure.append(new_rate)
        return {'id': new_rate['id']}
    
    def delete_rate(self, id):
        self.rate_structure = filter(lambda repayment: repayment['id'] != id, self.rate_structure)
        return True
        
    def calc(self):
        #get all term changes
        complex_loan = []
        amnt = self.principal
        breaks = sorted(set([i['month'] for i in self.rate_structure + self.repayment_structure]))
        print breaks
        rate = self.rate_structure[0]
        repayment = self.repayment_structure[0]
        for i, p in enumerate(breaks):
            payment = filter(lambda repayment: repayment['month'] == p and repayment['once_off'], self.repayment_structure)
            interest = filter(lambda repayment: repayment['month'] == p, self.rate_structure)
            rate = interest[0] if interest else rate
            amnt -= sum(pmt['payment'] for pmt in payment)
            for pmt in payment:
                complex_loan.append({'once_off': True, 'month': p, 'principal_paid': Decimal(str(pmt['payment']))})
            if i == len(breaks)-1:
                cutoff = -1
                months = self.months - p
            else:
                cutoff = breaks[i + 1]
                months = cutoff - p
            min_repayment = self.generate_repayment(amnt, rate['rate' ], self.months - p)
            if self.auto_adjust:
                payment = {'id': unicode(uuid.uuid4().hex), 'month': p, 'payment': min_repayment, 'once_off': False}
                self.repayment_structure.append(payment)

            repayment_option = filter(lambda repayment: repayment['month'] == p and not repayment['once_off'], self.repayment_structure)
            repayment = repayment_option if repayment_option else repayment

            complex_loan.append({'amnt': amnt, 'rate': rate['rate'], 'months': months, 'repayment': payment['payment'], 'cutoff': months, 'offset': p, 'min_repayment': min_repayment})
            segment = self.generate_mortgage_info(amnt, rate['rate'], months, payment['payment'], months, p)
            if segment:
                complex_loan += (segment)
                amnt = float(segment[-1]['principal'])
        return complex_loan
        #return self.generate_mortgage_info(self.principal, self.rate_structure[0]['rate'], self.months, self.repayment_structure[0]['payment'])
        
    def generate_repayment(self, principal, rate, months):
        repayment = principal * (rate / 12 * math.pow((1 + rate / 12), months)) / (math.pow((1 + rate / 12), months) - 1)
        return repayment
    
    def generate_mortgage_info(self, principal, rate, months = 240, repayment = 0, cutoff = 0, offset = 0):
        cutoff = months if cutoff <= 0 else cutoff
        
        d1 = Decimal('1.00')
        m_list = []
        if not repayment:
            repayment = self.generate_repayment(principal, rate, months)
        for month in range( offset + 1, cutoff + offset + 1 ):
            interest = rate / 12 * principal
    
            if repayment > principal:
                repayment = principal + interest
            principal += interest - repayment
            principal_paid = repayment - interest
            month_figures = {'month': month, 'once_off': False}
            for val in [('repayment', repayment), ('interest', interest), ('principal_paid', principal_paid), ('principal', principal)]:
                month_figures[val[0]] = (Decimal(str(val[1])).quantize(d1))
            m_list.append(month_figures)
            if principal <= 0:
                break
        return m_list
        
    def print_mortgage_info(self):
        info = self.calc()
        for month in info:
            if month.get('once_off') or month.get('amnt'):
                print month
            else:
                print '%(month)5d: %(repayment)5.2f - %(interest)10.2f - %(principal_paid)10.2f - %(principal)10.2f'%month


def example():
    x = Loan(700000, 0.095, auto_adjust=True)
    x.add_new_repayment(12, 1600)
    x.add_new_repayment(15, 1600)
    x.add_new_repayment(19, 1600)
    x.add_new_repayment(1, 2600)
    x.add_new_rate(24, 0.08)
    x.add_new_rate(48, 0.1)
    x.print_mortgage_info()
    
if __name__ == '__main__':
    example()