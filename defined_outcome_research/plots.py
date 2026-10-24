"""Original result figures; issuer artwork is never copied."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

NAVY="#101928"; TEAL="#168b85"; GOLD="#bc7b1c"; BLUE="#5679a6"


def save(fig, path):
    fig.savefig(path,dpi=170,bbox_inches="tight",metadata={"Software":"defined-outcome-research"})
    plt.close(fig)


def create_figures(out: Path, payoff, entries, fee_rows, fair_rows, marks, allocations, metric):
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,
                        "axes.spines.right":False,"axes.labelcolor":NAVY,"text.color":NAVY,"axes.titleweight":"bold"})
    fig,ax=plt.subplots(figsize=(9,5.1))
    ax.plot(payoff.reference_return,payoff.reference_return,label="Underlying price return",color=BLUE,ls="--")
    ax.plot(payoff.reference_return,payoff.target_return,label="BJAN terms: gross target shape",color=TEAL,lw=2.4)
    ax.plot(payoff.reference_return,payoff.funded_buffer_return,label="Same strike strip / model entry cost",color=GOLD,lw=1.8)
    ax.plot(payoff.reference_return,payoff.funded_protective_return,label="Protective put / model entry cost",color=NAVY,lw=1.5)
    ax.plot(payoff.reference_return,payoff.cash_return,label="Cash at model rate",color="#8d98a5",lw=1,ls=":")
    ax.axvspan(-.09,0,color=TEAL,alpha=.08)
    ax.axhline(0,color="#aab3c2",lw=.8);ax.set(xlim=(-.6,.6),ylim=(-.65,.7),xlabel="Reference return since original start",ylabel="Terminal return",title="A payoff diagram does not determine the entry cost")
    ax.xaxis.set_major_formatter(PercentFormatter(1));ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(loc="upper left",fontsize=8.7)
    fig.text(.13,.01,"Published terms + synthetic European marks; no ETF performance or quotes.",fontsize=8.3)
    save(fig,out/'payoff_and_cost.png')

    fig,axes=plt.subplots(1,2,figsize=(10.8,4.7),sharey=True)
    base=entries[entries.volatility.eq(.2)]
    for ax,col,title in zip(axes,['max_return_net','flat_original_return_net'],['Maximum terminal return','Return if reference finishes at original 100']):
        matrix=base.pivot(index='entry_spot',columns='elapsed_years',values=col).sort_index(ascending=False)
        image=ax.imshow(matrix.to_numpy(),cmap='BrBG',vmin=-.20,vmax=.20,aspect='auto')
        ax.set_xticks(range(4),['0','3','6','9']);ax.set_yticks(range(3),[str(int(x)) for x in matrix.index])
        ax.set(xlabel='Months elapsed at entry',title=title)
        for i in range(3):
            for j in range(4):ax.text(j,i,f'{matrix.iloc[i,j]:.1%}',ha='center',va='center',fontsize=11,color=NAVY,bbox=dict(facecolor='white',alpha=.7,edgecolor='none',pad=2))
    axes[0].set_ylabel('Reference level at entry (original = 100)')
    fig.suptitle('The original buffer is not a personal loss guarantee',fontsize=13,fontweight='bold')
    fig.subplots_adjust(top=.82,bottom=.18,wspace=.12)
    fig.text(.12,.03,'Model scenarios: volatility 20%, rate 3%, annual fee 0.79%; entry cost is recomputed.',fontsize=8.5)
    save(fig,out/'entry_time.png')

    fig,ax=plt.subplots(figsize=(9,4.8))
    for tau,color in [(1,BLUE),(.5,GOLD),(.25,TEAL),(0,NAVY)]:
        frame=marks[marks.remaining_years.eq(tau)]
        ax.plot(frame.spot,frame.value,label=f'{tau:g} years remaining',color=color,lw=2 if tau==0 else 1.6)
    ax.set(xlim=(60,140),ylim=(65,118),xlabel='Current reference level (original = 100)',ylabel='Gross value per model claim',title='Interim value includes time value and discounting')
    ax.legend(fontsize=9);fig.subplots_adjust(bottom=.23)
    fig.text(.13,.02,'Constant 20% volatility, 3% rate, zero dividend yield; marks are not tradable quotes.',fontsize=8.3)
    save(fig,out/'interim_value.png')

    fig,axes=plt.subplots(1,2,figsize=(10.8,4.7))
    x=np.arange(3); labels=['Gross\nterms','Issuer-published\nnet cap','Unit-depletion\nillustration']
    vals=[metric['issuer_cap_gross'],metric['issuer_cap_net'],metric['unit_depletion_target_cap']]
    axes[0].bar(x,vals,color=[BLUE,TEAL,GOLD],width=.6)
    for i,v in enumerate(vals):axes[0].text(i,v+.002,f'{v:.2%}',ha='center',fontsize=10)
    axes[0].set_xticks(x,labels,fontsize=8);axes[0].set(ylim=(0,.19),ylabel='Cap / terminal return',title='Two fee conventions, kept separate')
    axes[0].yaxis.set_major_formatter(PercentFormatter(1))
    for b,color in [(.05,BLUE),(.09,TEAL),(.15,GOLD)]:
        frame=fair_rows[fair_rows.buffer.eq(b)]
        axes[1].plot(frame.volatility,frame.fair_cap,marker='o',label=f'{b:.0%} buffer',color=color)
    axes[1].set(xlabel='Assumed volatility',ylabel='Model budget-balanced cap',title='A richer buffer consumes option budget')
    axes[1].set_xticks([.1,.2,.4]);axes[1].xaxis.set_major_formatter(PercentFormatter(1));axes[1].yaxis.set_major_formatter(PercentFormatter(1));axes[1].legend(fontsize=9)
    fig.subplots_adjust(bottom=.22,wspace=.34,top=.88)
    fig.text(.09,.04,'Left: published arithmetic net terms vs a distinct fee-unit scenario; neither is a fund NAV forecast.\nRight: European price-claim budget = 100, rate 3%, one year, zero dividend yield.',fontsize=8.3)
    save(fig,out/'fees_and_option_budget.png')

    fig,ax=plt.subplots(figsize=(8.8,4.5))
    labels=[f"${int(v):,}" for v in allocations.budget]
    debit=allocations.initial_debit/allocations.budget
    cash=allocations.cash/allocations.budget
    ax.bar(labels,debit,label='Package debit incl. friction',color=TEAL)
    ax.bar(labels,cash,bottom=debit,label='Uninvested cash',color='#b8c7d7')
    for i,row in enumerate(allocations.itertuples()):ax.text(i,1.015,f'{row.packages} packages',ha='center')
    ax.set(ylim=(0,1.12),ylabel='Share of initial budget',xlabel='Illustrative budget',title='Integer packages create cash drag and infeasibility')
    ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(loc='lower right',fontsize=9)
    fig.subplots_adjust(bottom=.23)
    fig.text(.13,.02,'Multiplier 100, entry half-spread 10 bps, $4/package commission; extra broker margin excluded.',fontsize=8.1)
    save(fig,out/'integer_budget.png')
